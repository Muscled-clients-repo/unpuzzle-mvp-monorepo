# Unpuzzle MVP Backend - Video Upload & Backblaze Integration Plan

**Date**: August 20, 2025  
**Time**: 19:22:27  
**Version**: 1.0  
**Status**: Implementation Plan

---

## Executive Summary

This document provides a comprehensive plan for implementing efficient video upload to Backblaze B2 Cloud Storage with file metadata management in the database. The solution includes CDN integration via Bunny.net for optimal video delivery performance.

### Key Objectives
- **Primary**: Implement secure, scalable video upload to Backblaze B2
- **Secondary**: Store comprehensive file metadata in database for efficient management
- **Performance**: Leverage Bunny.net CDN for fast global video delivery
- **User Experience**: Provide upload progress tracking and video processing status

---

## Current System Analysis

### Existing Database Models

Based on analysis of the current codebase, we have:

**Video Model** (`app/models/course/video.py`):
```python
class Video(AuditableModel):
    # Current fields relevant to file storage
    video_url = Column(Text, nullable=False)        # Currently stores direct URLs
    video_provider = Column(String(50), default='vimeo', nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    video_metadata = Column('metadata', JSON, nullable=True)
```

**Current Limitations**:
- No file storage metadata tracking
- No upload tracking or processing status
- Limited file format/quality information
- No CDN optimization tracking

---

## Proposed Database Schema Enhancements

### 1. New `MediaFile` Model

Create a comprehensive file storage model:

```python
# app/models/storage/media_file.py
from sqlalchemy import Column, String, Text, Integer, Boolean, JSON, DateTime, BigInteger, Float
from app.models.base import AuditableModel
import enum

class FileType(str, enum.Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class StorageProvider(str, enum.Enum):
    BACKBLAZE = "backblaze"
    LOCAL = "local"
    AWS_S3 = "aws_s3"

class MediaFile(AuditableModel):
    """Media file storage with comprehensive metadata"""
    __tablename__ = "media_files"
    
    # File identification
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)  # Path in storage
    file_type = Column(String(50), nullable=False)  # video, audio, image, etc
    mime_type = Column(String(100), nullable=False)
    
    # Storage information
    storage_provider = Column(String(50), default=StorageProvider.BACKBLAZE.value, nullable=False)
    bucket_name = Column(String(100), nullable=False)
    storage_key = Column(Text, nullable=False)  # Unique key in storage
    storage_url = Column(Text, nullable=False)  # Direct storage URL
    cdn_url = Column(Text, nullable=True)  # CDN URL for delivery
    
    # File metadata
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    checksum = Column(String(64), nullable=True)  # MD5 or SHA256
    
    # Processing status
    processing_status = Column(String(50), default=ProcessingStatus.PENDING.value, nullable=False)
    upload_progress = Column(Float, default=0.0, nullable=False)  # 0-100
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Media-specific metadata
    duration_seconds = Column(Integer, nullable=True)  # For video/audio
    width = Column(Integer, nullable=True)  # For images/video
    height = Column(Integer, nullable=True)  # For images/video
    bitrate = Column(Integer, nullable=True)  # For video/audio
    codec = Column(String(50), nullable=True)
    frame_rate = Column(Float, nullable=True)  # For video
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    tags = Column(JSON, default=list)
    
    # Usage tracking
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    video_content = relationship("Video", back_populates="media_file", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_media_file_type_status', 'file_type', 'processing_status'),
        Index('idx_media_storage_key', 'storage_provider', 'storage_key'),
        Index('idx_media_checksum', 'checksum'),
    )
```

### 2. Enhanced `Video` Model

Update the existing Video model to reference MediaFile:

```python
# Modifications to app/models/course/video.py
class Video(AuditableModel):
    # ... existing fields ...
    
    # New relationship to media file
    media_file_id = Column(String(36), ForeignKey('media_files.id'), nullable=True, index=True)
    media_file = relationship("MediaFile", back_populates="video_content")
    
    # Keep legacy fields for backward compatibility
    video_url = Column(Text, nullable=True)  # Make nullable, fallback to media_file
    video_provider = Column(String(50), default='backblaze', nullable=False)
    
    # New fields for enhanced functionality
    video_quality = Column(String(20), default='720p', nullable=False)  # 480p, 720p, 1080p, 4k
    has_captions = Column(Boolean, default=False, nullable=False)
    caption_languages = Column(JSON, default=list)
    
    def get_video_url(self) -> str:
        """Get the best available video URL (CDN preferred)"""
        if self.media_file:
            return self.media_file.cdn_url or self.media_file.storage_url
        return self.video_url
    
    def get_video_metadata(self) -> dict:
        """Get comprehensive video metadata"""
        if self.media_file:
            return {
                'duration': self.media_file.duration_seconds,
                'resolution': f"{self.media_file.width}x{self.media_file.height}" if self.media_file.width else None,
                'bitrate': self.media_file.bitrate,
                'codec': self.media_file.codec,
                'fileSize': self.media_file.file_size,
                'processingStatus': self.media_file.processing_status
            }
        return self.video_metadata or {}
```

### 3. Upload Tracking Model

Track upload sessions and progress:

```python
# app/models/storage/upload_session.py
class UploadSession(AuditableModel):
    """Track file upload sessions for progress monitoring"""
    __tablename__ = "upload_sessions"
    
    # Session identification
    session_key = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    
    # Upload details
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100), nullable=False)
    
    # Progress tracking
    bytes_uploaded = Column(BigInteger, default=0, nullable=False)
    upload_progress = Column(Float, default=0.0, nullable=False)  # 0-100
    
    # Status
    status = Column(String(50), default='pending', nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Result
    media_file_id = Column(String(36), ForeignKey('media_files.id'), nullable=True)
    media_file = relationship("MediaFile")
    
    # Relationships
    user = relationship("User")
```

---

## Implementation Architecture

### 1. Storage Service Layer

Create a comprehensive storage service:

```python
# app/services/storage_service.py
import boto3
from botocore.exceptions import ClientError
import hashlib
import mimetypes
from typing import Optional, Dict, Any, BinaryIO
from app.core.config import settings
from app.models.storage.media_file import MediaFile, ProcessingStatus, StorageProvider
from app.models.storage.upload_session import UploadSession

class BackblazeStorageService:
    """Backblaze B2 storage service with comprehensive file management"""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=f'https://{settings.BB_ENDPOINT}',
            aws_access_key_id=settings.BB_KEY_ID,
            aws_secret_access_key=settings.BB_APPLICATION_KEY,
            region_name='us-west-002'
        )
        self.bucket_name = settings.BB_BUCKET_ID
        self.cdn_base_url = settings.CDN_URL
    
    async def upload_file(
        self, 
        file_stream: BinaryIO, 
        filename: str,
        content_type: str,
        user_id: str,
        progress_callback: Optional[callable] = None
    ) -> MediaFile:
        """
        Upload file to Backblaze with progress tracking
        """
        # Generate unique storage key
        file_hash = hashlib.md5(f"{user_id}-{filename}".encode()).hexdigest()
        storage_key = f"videos/{user_id}/{file_hash}_{filename}"
        
        # Create upload session
        session = UploadSession(
            session_key=file_hash,
            user_id=user_id,
            filename=filename,
            file_size=len(file_stream.read()),
            content_type=content_type,
            status='uploading'
        )
        
        # Reset file pointer
        file_stream.seek(0)
        
        try:
            # Calculate file checksum
            file_content = file_stream.read()
            file_checksum = hashlib.md5(file_content).hexdigest()
            file_stream.seek(0)
            
            # Upload to Backblaze
            extra_args = {
                'ContentType': content_type,
                'Metadata': {
                    'user-id': user_id,
                    'original-filename': filename,
                    'checksum': file_checksum
                }
            }
            
            self.client.upload_fileobj(
                file_stream,
                self.bucket_name,
                storage_key,
                ExtraArgs=extra_args,
                Callback=progress_callback
            )
            
            # Generate URLs
            storage_url = f"https://{self.bucket_name}.{settings.BB_ENDPOINT}/{storage_key}"
            cdn_url = f"{self.cdn_base_url}/{storage_key}"
            
            # Create MediaFile record
            media_file = MediaFile(
                filename=filename,
                original_filename=filename,
                file_path=storage_key,
                file_type='video',
                mime_type=content_type,
                storage_provider=StorageProvider.BACKBLAZE.value,
                bucket_name=self.bucket_name,
                storage_key=storage_key,
                storage_url=storage_url,
                cdn_url=cdn_url,
                file_size=len(file_content),
                checksum=file_checksum,
                processing_status=ProcessingStatus.COMPLETED.value,
                upload_progress=100.0,
                processing_completed_at=func.now()
            )
            
            # Update session
            session.status = 'completed'
            session.completed_at = func.now()
            session.upload_progress = 100.0
            session.media_file = media_file
            
            return media_file
            
        except ClientError as e:
            session.status = 'failed'
            session.error_message = str(e)
            raise Exception(f"Upload failed: {e}")
    
    def get_presigned_upload_url(self, storage_key: str, content_type: str) -> Dict[str, Any]:
        """Generate presigned URL for direct browser upload"""
        try:
            response = self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=storage_key,
                Fields={'Content-Type': content_type},
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, 500 * 1024 * 1024]  # 500MB max
                ],
                ExpiresIn=3600  # 1 hour
            )
            return response
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {e}")
    
    def delete_file(self, storage_key: str) -> bool:
        """Delete file from Backblaze"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=storage_key)
            return True
        except ClientError as e:
            return False
```

### 2. Video Processing Service

Handle video metadata extraction and processing:

```python
# app/services/video_processing_service.py
import ffmpeg
from typing import Dict, Any, Optional
from app.models.storage.media_file import MediaFile

class VideoProcessingService:
    """Service for video processing and metadata extraction"""
    
    @staticmethod
    def extract_metadata(file_path: str) -> Dict[str, Any]:
        """Extract video metadata using ffmpeg"""
        try:
            probe = ffmpeg.probe(file_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            metadata = {
                'duration': float(probe['format']['duration']),
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'codec': video_stream['codec_name'],
                'bitrate': int(video_stream.get('bit_rate', 0)),
                'frame_rate': eval(video_stream['r_frame_rate']) if 'r_frame_rate' in video_stream else None,
                'format': probe['format']['format_name']
            }
            
            return metadata
            
        except Exception as e:
            raise Exception(f"Failed to extract metadata: {e}")
    
    @staticmethod
    def generate_thumbnail(video_url: str, output_path: str, timestamp: float = 10.0) -> str:
        """Generate thumbnail from video at specified timestamp"""
        try:
            (
                ffmpeg
                .input(video_url, ss=timestamp)
                .filter('scale', 320, 240)
                .output(output_path, vframes=1, format='image2', vcodec='mjpeg')
                .overwrite_output()
                .run(quiet=True)
            )
            return output_path
        except Exception as e:
            raise Exception(f"Failed to generate thumbnail: {e}")
```

### 3. Enhanced API Endpoints

Create comprehensive video upload API:

```python
# app/api/v1/videos.py (additions)
from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
import uuid
from app.services.storage_service import BackblazeStorageService
from app.services.video_processing_service import VideoProcessingService
from app.middleware.auth_middleware import require_auth
from app.core.security import create_response

@videos_bp.route('/upload/initiate', methods=['POST'])
@require_auth
def initiate_upload():
    """Initiate video upload process"""
    data = request.get_json()
    
    filename = data.get('filename')
    file_size = data.get('fileSize')
    content_type = data.get('contentType')
    
    if not all([filename, file_size, content_type]):
        return jsonify(create_response(False, error="Missing required fields")), 400
    
    # Validate file type
    allowed_types = ['video/mp4', 'video/webm', 'video/avi', 'video/mov']
    if content_type not in allowed_types:
        return jsonify(create_response(False, error="Unsupported file type")), 400
    
    # Generate upload session
    storage_service = BackblazeStorageService()
    session_key = str(uuid.uuid4())
    storage_key = f"videos/{g.user_id}/{session_key}_{secure_filename(filename)}"
    
    # Get presigned upload URL
    presigned_data = storage_service.get_presigned_upload_url(storage_key, content_type)
    
    # Create upload session record
    session = UploadSession(
        session_key=session_key,
        user_id=g.user_id,
        filename=filename,
        file_size=file_size,
        content_type=content_type,
        status='pending'
    )
    
    return jsonify(create_response(True, data={
        'sessionKey': session_key,
        'uploadUrl': presigned_data['url'],
        'fields': presigned_data['fields']
    }))

@videos_bp.route('/upload/complete', methods=['POST'])
@require_auth
def complete_upload():
    """Complete video upload and process metadata"""
    data = request.get_json()
    session_key = data.get('sessionKey')
    
    # Find upload session
    session = UploadSession.query.filter_by(session_key=session_key, user_id=g.user_id).first()
    if not session:
        return jsonify(create_response(False, error="Invalid session")), 404
    
    try:
        # Extract video metadata (this would be done asynchronously in production)
        storage_service = BackblazeStorageService()
        processing_service = VideoProcessingService()
        
        # Create MediaFile record
        media_file = MediaFile(
            filename=session.filename,
            original_filename=session.filename,
            file_path=f"videos/{g.user_id}/{session_key}_{session.filename}",
            file_type='video',
            mime_type=session.content_type,
            storage_provider='backblaze',
            bucket_name=settings.BB_BUCKET_ID,
            storage_key=f"videos/{g.user_id}/{session_key}_{session.filename}",
            storage_url=f"https://{settings.BB_BUCKET_ID}.{settings.BB_ENDPOINT}/videos/{g.user_id}/{session_key}_{session.filename}",
            cdn_url=f"{settings.CDN_URL}/videos/{g.user_id}/{session_key}_{session.filename}",
            file_size=session.file_size,
            processing_status='completed'
        )
        
        # Update session
        session.status = 'completed'
        session.media_file = media_file
        
        return jsonify(create_response(True, data={
            'mediaFileId': media_file.id,
            'cdnUrl': media_file.cdn_url
        }))
        
    except Exception as e:
        session.status = 'failed'
        session.error_message = str(e)
        return jsonify(create_response(False, error="Upload processing failed")), 500

@videos_bp.route('/upload/progress/<session_key>', methods=['GET'])
@require_auth
def get_upload_progress(session_key):
    """Get upload progress"""
    session = UploadSession.query.filter_by(session_key=session_key, user_id=g.user_id).first()
    if not session:
        return jsonify(create_response(False, error="Session not found")), 404
    
    return jsonify(create_response(True, data={
        'status': session.status,
        'progress': session.upload_progress,
        'error': session.error_message
    }))
```

---

## Database Migration Strategy

### Migration Scripts

```sql
-- Add new tables
CREATE TABLE media_files (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    storage_provider VARCHAR(50) NOT NULL DEFAULT 'backblaze',
    bucket_name VARCHAR(100) NOT NULL,
    storage_key TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    cdn_url TEXT,
    file_size BIGINT NOT NULL,
    checksum VARCHAR(64),
    processing_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    upload_progress FLOAT NOT NULL DEFAULT 0.0,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    processing_error TEXT,
    duration_seconds INTEGER,
    width INTEGER,
    height INTEGER,
    bitrate INTEGER,
    codec VARCHAR(50),
    frame_rate FLOAT,
    metadata JSON,
    tags JSON DEFAULT '[]',
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_id VARCHAR(36),
    updated_by_id VARCHAR(36),
    deleted_by_id VARCHAR(36),
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE upload_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_key VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    bytes_uploaded BIGINT NOT NULL DEFAULT 0,
    upload_progress FLOAT NOT NULL DEFAULT 0.0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    media_file_id VARCHAR(36) REFERENCES media_files(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    version INTEGER NOT NULL DEFAULT 1
);

-- Add media_file_id to videos table
ALTER TABLE videos ADD COLUMN media_file_id VARCHAR(36) REFERENCES media_files(id);
ALTER TABLE videos ADD COLUMN video_quality VARCHAR(20) NOT NULL DEFAULT '720p';
ALTER TABLE videos ADD COLUMN has_captions BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE videos ADD COLUMN caption_languages JSON DEFAULT '[]';

-- Create indexes
CREATE INDEX idx_media_file_type_status ON media_files(file_type, processing_status);
CREATE INDEX idx_media_storage_key ON media_files(storage_provider, storage_key);
CREATE INDEX idx_media_checksum ON media_files(checksum);
CREATE INDEX idx_upload_session_key ON upload_sessions(session_key);
CREATE INDEX idx_upload_user_status ON upload_sessions(user_id, status);
```

---

## Configuration Updates

### Environment Variables

Add to `.env`:

```bash
# Backblaze B2 Configuration (already added)
BB_KEY_ID="0022aa493f0b93f0000000001"
BB_KEY_NAME=unpuzzl
BB_APPLICATION_KEY="K002tqaSq0yUCdbbwnr6D5G5x1JHGmU"
BB_ENDPOINT="s3.us-west-002.backblazeb2.com"
BB_BUCKET_ID="b20a0a2459434f709b49031f"

# CDN Configuration (already added)
CDN_URL="https://unpuzzle.b-cdn.net"

# Video Processing Configuration
MAX_VIDEO_SIZE_MB=500
ALLOWED_VIDEO_FORMATS=mp4,webm,avi,mov
VIDEO_PROCESSING_QUEUE=video_processing
THUMBNAIL_GENERATION_ENABLED=true

# Upload Configuration
UPLOAD_SESSION_TIMEOUT=3600  # 1 hour
MAX_CONCURRENT_UPLOADS=5
CHUNK_SIZE_MB=5
```

### Dependencies

Add to `requirements.txt`:

```
boto3==1.34.40
ffmpeg-python==0.2.0
Pillow==10.2.0
celery==5.3.4  # For background processing
redis==5.0.1   # For task queue
```

---

## Implementation Phases

### Phase 1: Database Schema & Models (Days 1-2)
1. Create migration scripts for new tables
2. Implement MediaFile and UploadSession models
3. Update Video model with new relationships
4. Test database operations

### Phase 2: Storage Service (Days 3-4)
1. Implement BackblazeStorageService
2. Add file upload with progress tracking
3. Implement presigned URL generation
4. Test upload/download operations

### Phase 3: Video Processing (Days 5-6)
1. Implement VideoProcessingService
2. Add metadata extraction using ffmpeg
3. Implement thumbnail generation
4. Set up background job processing

### Phase 4: API Endpoints (Days 7-8)
1. Create upload initiation endpoint
2. Implement upload completion handling
3. Add progress tracking endpoint
4. Create video management endpoints

### Phase 5: Integration & Testing (Days 9-10)
1. Update existing video creation workflow
2. Implement data migration for existing videos
3. Add comprehensive error handling
4. Performance testing and optimization

---

## Performance Considerations

### 1. Upload Optimization
- **Chunked Upload**: Large files uploaded in chunks for reliability
- **Progress Tracking**: Real-time upload progress via WebSocket
- **Background Processing**: Metadata extraction happens asynchronously

### 2. CDN Integration
- **Edge Caching**: Videos cached at CDN edge locations
- **Adaptive Streaming**: Multiple quality versions for different bandwidths
- **Geographic Distribution**: Global content delivery

### 3. Database Optimization
- **Indexed Queries**: Strategic indexes on frequently queried fields
- **Denormalized Data**: Cache video metadata in video table for performance
- **Connection Pooling**: Efficient database connection management

### 4. Monitoring & Analytics
- **Upload Success Rate**: Track successful vs failed uploads
- **Processing Time**: Monitor video processing performance
- **Storage Usage**: Track storage consumption per user/course

---

## Security Considerations

### 1. File Upload Security
- **File Type Validation**: Strict MIME type checking
- **Size Limits**: Maximum file size enforcement
- **Virus Scanning**: Optional malware detection
- **User Quotas**: Storage limits per user/organization

### 2. Access Control
- **Signed URLs**: Time-limited access to video content
- **User Authorization**: Course enrollment verification
- **Rate Limiting**: Prevent upload abuse

### 3. Data Protection
- **Encryption in Transit**: HTTPS for all uploads
- **Encryption at Rest**: Backblaze B2 server-side encryption
- **Audit Trail**: Complete upload/access logging

---

## Cost Optimization

### 1. Storage Costs
- **Lifecycle Policies**: Archive old/unused videos
- **Compression**: Optimal video encoding for size/quality balance
- **Duplicate Detection**: Prevent duplicate file uploads

### 2. CDN Costs
- **Cache Optimization**: Maximize cache hit ratios
- **Bandwidth Management**: Monitor and optimize delivery costs
- **Regional Distribution**: Strategic CDN node utilization

### 3. Processing Costs
- **Efficient Processing**: Optimize video processing workflows
- **Resource Scaling**: Scale processing resources based on demand

---

## Monitoring & Observability

### 1. Metrics to Track
- Upload success/failure rates
- Processing time per video
- Storage usage growth
- CDN cache hit rates
- User engagement with video content

### 2. Alerting
- Failed upload notifications
- Storage quota warnings
- Processing errors
- CDN performance issues

### 3. Logging
- Structured logging for all upload operations
- Error tracking with stack traces
- Performance metrics collection

---

## Next Steps

1. **Review and Approve**: Review this plan with development team
2. **Environment Setup**: Configure Backblaze and Bunny.net accounts
3. **Database Migration**: Execute schema changes in development
4. **Phased Implementation**: Begin Phase 1 implementation
5. **Testing Strategy**: Develop comprehensive test plan
6. **Production Deployment**: Plan production rollout strategy

---

**Status**: Ready for Implementation  
**Estimated Timeline**: 10 development days  
**Risk Level**: Medium (external service dependencies)  
**Success Criteria**: Efficient video upload with < 5% failure rate, CDN delivery < 2s globally