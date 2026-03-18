import os
import json
import logging
from datetime import datetime
from backend.db_service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_models_to_database():
    db = DatabaseService()
    
    try:
        if not db.is_connected():
            db.connect()
        
        versions_dir = "backend/model/versions"
        
        if not os.path.exists(versions_dir):
            logger.error(f"Versions directory not found: {versions_dir}")
            return
        
        version_folders = [f for f in os.listdir(versions_dir) if os.path.isdir(os.path.join(versions_dir, f))]
        version_folders.sort()
        
        logger.info(f"Found {len(version_folders)} version folders: {version_folders}")
        
        for version in version_folders:
            version_path = os.path.join(versions_dir, version)
            
            autoencoder_path = os.path.join(version_path, "autoencoder")
            if os.path.exists(autoencoder_path):
                migrate_model(db, version, "Autoencoder", autoencoder_path)
            
            isolation_forest_path = os.path.join(version_path, "isolation_forest")
            if os.path.exists(isolation_forest_path):
                migrate_model(db, version, "Isolation Forest", isolation_forest_path)
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        if db.is_connected():
            db.disconnect()

def migrate_model(db, version, model_name, model_path):
    try:
        metadata_file = os.path.join(model_path, "metadata.json")
        if not os.path.exists(metadata_file):
            logger.warning(f"Metadata file not found: {metadata_file}")
            return
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        metrics = metadata.get('metrics', {})
        model_type = metadata.get('model_type', '').lower()
        
        model_file_path = f"backend/model/versions/{version}/{model_type}/model.pkl"
        scaler_path = f"backend/model/versions/{version}/{model_type}/scaler.pkl"
        threshold_path = f"backend/model/versions/{version}/{model_type}/threshold.json" if model_type == "autoencoder" else None
        
        check_query = "SELECT COUNT(*) FROM ModelVersionConfig WHERE ModelName = %s AND VersionNumber = %s"
        result = db.execute_query(check_query, [model_name, version])
        
        if result and result[0][0] > 0:
            logger.info(f"Entry already exists for {model_name} v{version}, skipping...")
            return
        
        if model_type == "autoencoder":
            accuracy = None
            precision = None
            recall = None
            f1_score = None
            training_data_size = metrics.get('n_samples', 0)
        else:
            accuracy = None
            precision = None
            recall = None
            f1_score = None
            training_data_size = metrics.get('n_samples', 0)
        
        timestamp_str = metadata.get('timestamp', '')
        try:
            created_at = datetime.fromisoformat(timestamp_str.replace('T', ' '))
        except:
            created_at = datetime.now()
        
        query = """
        INSERT INTO ModelVersionConfig 
        (ModelName, VersionNumber, ModelPath, ScalerPath, ThresholdPath, IsActive, 
         Accuracy, Precision, Recall, F1Score, CreatedAt, TrainingDataSize, ModelSize, CreatedBy, Notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = [
            model_name,
            version,
            model_file_path,
            scaler_path,
            threshold_path,
            0,
            accuracy,
            precision,
            recall,
            f1_score,
            created_at,
            training_data_size,
            0,
            "Migration Script",
            f"Migrated from filesystem - Original timestamp: {timestamp_str}"
        ]
        
        db.execute_non_query(query, params)
        logger.info(f"Successfully migrated {model_name} version {version}")
        
    except Exception as e:
        logger.error(f"Error migrating {model_name} v{version}: {e}")

if __name__ == "__main__":
    print("Model Migration Script")
    print("=====================")
    print("This script will migrate existing model versions to the database.")
    print("Make sure the database is running and accessible.")
    print()
    
    confirm = input("Do you want to proceed? (y/N): ")
    if confirm.lower() in ['y', 'yes']:
        migrate_models_to_database()
    else:
        print("Migration cancelled.")