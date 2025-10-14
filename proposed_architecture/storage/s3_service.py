"""
S3 Storage Service for Evaluation System
Handles file uploads, downloads, and backups to S3
"""

import boto3
import os
import hashlib
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import shutil


class S3StorageService:
    """Service for managing files in S3"""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = 'us-east-1',
        local_cache_dir: str = '/home/cdsw/evaluation_cache'
    ):
        """
        Initialize S3 service

        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key (or use env/IAM role)
            aws_secret_access_key: AWS secret key (or use env/IAM role)
            region_name: AWS region
            local_cache_dir: Local directory for caching downloaded files
        """
        self.bucket_name = bucket_name
        self.local_cache_dir = Path(local_cache_dir)
        self.local_cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize S3 client
        session_kwargs = {'region_name': region_name}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs['aws_access_key_id'] = aws_access_key_id
            session_kwargs['aws_secret_access_key'] = aws_secret_access_key

        self.s3_client = boto3.client('s3', **session_kwargs)

    def upload_file(
        self,
        local_file_path: str,
        s3_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to S3

        Args:
            local_file_path: Path to local file
            s3_key: S3 object key (path in bucket)
            metadata: Optional metadata to attach to file

        Returns:
            Dict with upload info (s3_key, size, checksum, etc.)
        """
        local_path = Path(local_file_path)

        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_file_path}")

        # Calculate checksum
        checksum = self._calculate_checksum(local_path)
        file_size = local_path.stat().st_size

        # Upload to S3
        extra_args = {}
        if metadata:
            extra_args['Metadata'] = metadata

        self.s3_client.upload_file(
            str(local_path),
            self.bucket_name,
            s3_key,
            ExtraArgs=extra_args
        )

        return {
            's3_bucket': self.bucket_name,
            's3_key': s3_key,
            'file_size': file_size,
            'checksum': checksum,
            'uploaded_at': datetime.now().isoformat()
        }

    def download_file(
        self,
        s3_key: str,
        local_file_path: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Download file from S3

        Args:
            s3_key: S3 object key
            local_file_path: Where to save file (optional)
            use_cache: If True, save to cache directory

        Returns:
            Path to downloaded file
        """
        # Determine local path
        if local_file_path:
            local_path = Path(local_file_path)
        elif use_cache:
            # Save to cache directory
            cache_path = self.local_cache_dir / s3_key.replace('/', '_')
            local_path = cache_path
        else:
            raise ValueError("Must provide local_file_path or set use_cache=True")

        # Create parent directories
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Download from S3
        self.s3_client.download_file(
            self.bucket_name,
            s3_key,
            str(local_path)
        )

        return str(local_path)

    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except:
            return False

    def get_file_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from S3"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {})
            }
        except:
            return None

    def list_files(self, prefix: str = '', max_keys: int = 1000) -> List[Dict[str, Any]]:
        """List files in S3 with given prefix"""
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix,
            MaxKeys=max_keys
        )

        files = []
        for obj in response.get('Contents', []):
            files.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat(),
                'etag': obj['ETag'].strip('"')
            })

        return files

    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except:
            return False

    def backup_database(
        self,
        db_file_path: str,
        backup_prefix: str = 'backups/database/'
    ) -> Dict[str, Any]:
        """
        Backup SQLite database to S3

        Args:
            db_file_path: Path to SQLite database file
            backup_prefix: S3 prefix for backups

        Returns:
            Dict with backup info
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"{backup_prefix}evaluation_system_{timestamp}.db"

        return self.upload_file(
            local_file_path=db_file_path,
            s3_key=s3_key,
            metadata={
                'backup_type': 'database',
                'timestamp': timestamp
            }
        )

    def restore_database(
        self,
        backup_s3_key: str,
        restore_path: str
    ) -> str:
        """
        Restore database from S3 backup

        Args:
            backup_s3_key: S3 key of backup file
            restore_path: Where to restore the database

        Returns:
            Path to restored database
        """
        return self.download_file(
            s3_key=backup_s3_key,
            local_file_path=restore_path,
            use_cache=False
        )

    def list_backups(self, backup_prefix: str = 'backups/database/') -> List[Dict[str, Any]]:
        """List all database backups"""
        return self.list_files(prefix=backup_prefix)

    def get_latest_backup(self, backup_prefix: str = 'backups/database/') -> Optional[Dict[str, Any]]:
        """Get the most recent backup"""
        backups = self.list_backups(backup_prefix)
        if not backups:
            return None

        # Sort by last_modified (descending)
        backups.sort(key=lambda x: x['last_modified'], reverse=True)
        return backups[0]

    def save_json_to_s3(
        self,
        data: Dict[str, Any],
        s3_key: str
    ) -> Dict[str, Any]:
        """
        Save JSON data directly to S3

        Args:
            data: Dictionary to save as JSON
            s3_key: S3 object key

        Returns:
            Upload info
        """
        # Save to temporary file
        temp_file = self.local_cache_dir / 'temp_json.json'
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Upload to S3
        result = self.upload_file(
            local_file_path=str(temp_file),
            s3_key=s3_key
        )

        # Clean up temp file
        temp_file.unlink()

        return result

    def load_json_from_s3(self, s3_key: str) -> Dict[str, Any]:
        """
        Load JSON data from S3

        Args:
            s3_key: S3 object key

        Returns:
            Parsed JSON data
        """
        # Download to temp file
        local_path = self.download_file(s3_key, use_cache=True)

        # Load JSON
        with open(local_path, 'r') as f:
            data = json.load(f)

        return data

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear local cache directory

        Args:
            older_than_days: Only delete files older than this many days
        """
        if older_than_days is None:
            # Delete everything
            shutil.rmtree(self.local_cache_dir)
            self.local_cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Delete old files
            cutoff_time = datetime.now().timestamp() - (older_than_days * 86400)
            for file_path in self.local_cache_dir.rglob('*'):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()


class S3FileManager:
    """High-level file manager that coordinates S3 and local storage"""

    def __init__(
        self,
        s3_service: S3StorageService,
        base_s3_prefix: str = 'evaluation_system/'
    ):
        """
        Initialize file manager

        Args:
            s3_service: S3 storage service instance
            base_s3_prefix: Base prefix for all S3 keys
        """
        self.s3 = s3_service
        self.base_prefix = base_s3_prefix

    def save_config_file(
        self,
        use_case_id: str,
        local_file_path: str
    ) -> Dict[str, Any]:
        """Save configuration file to S3"""
        s3_key = f"{self.base_prefix}configs/{use_case_id}/config.yaml"
        return self.s3.upload_file(
            local_file_path=local_file_path,
            s3_key=s3_key,
            metadata={'type': 'config', 'use_case_id': use_case_id}
        )

    def save_dataset_file(
        self,
        use_case_id: str,
        local_file_path: str
    ) -> Dict[str, Any]:
        """Save dataset file to S3"""
        file_ext = Path(local_file_path).suffix
        s3_key = f"{self.base_prefix}datasets/{use_case_id}/dataset{file_ext}"
        return self.s3.upload_file(
            local_file_path=local_file_path,
            s3_key=s3_key,
            metadata={'type': 'dataset', 'use_case_id': use_case_id}
        )

    def save_results_file(
        self,
        use_case_id: str,
        local_file_path: str,
        result_type: str = 'evaluation'
    ) -> Dict[str, Any]:
        """Save evaluation results to S3"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_ext = Path(local_file_path).suffix
        s3_key = f"{self.base_prefix}results/{use_case_id}/{result_type}_{timestamp}{file_ext}"
        return self.s3.upload_file(
            local_file_path=local_file_path,
            s3_key=s3_key,
            metadata={'type': 'results', 'use_case_id': use_case_id}
        )

    def get_config_file(self, use_case_id: str) -> str:
        """Download config file from S3"""
        s3_key = f"{self.base_prefix}configs/{use_case_id}/config.yaml"
        return self.s3.download_file(s3_key, use_cache=True)

    def get_dataset_file(self, use_case_id: str, file_extension: str = '.csv') -> str:
        """Download dataset file from S3"""
        s3_key = f"{self.base_prefix}datasets/{use_case_id}/dataset{file_extension}"
        return self.s3.download_file(s3_key, use_cache=True)
