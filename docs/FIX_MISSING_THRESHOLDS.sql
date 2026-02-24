-- Fix: Add missing thresholds to ThresholdConfig table
-- These are required by hybrid_decision.py

-- Check if thresholds exist
SELECT ThresholdName, ThresholdValue FROM ThresholdConfig 
WHERE ThresholdName IN (
    'IF_Anomaly_High',
    'IF_Anomaly_Medium', 
    'IF_Anomaly_Low',
    'Confidence_AllAgree',
    'Confidence_TwoAgree',
    'Confidence_OneAgrees',
    'Confidence_HighRiskBoost'
);

-- Insert missing thresholds if they don't exist
INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, IsActive)
SELECT 'IF_Anomaly_High', 'isolation_forest', 0.85, 0.5, 1.0, 'High risk threshold for Isolation Forest', 1
WHERE NOT EXISTS (SELECT 1 FROM ThresholdConfig WHERE ThresholdName = 'IF_Anomaly_High');

INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, IsActive)
SELECT 'IF_Anomaly_Medium', 'isolation_forest', 0.65, 0.3, 0.9, 'Medium risk threshold for Isolation Forest', 1
WHERE NOT EXISTS (SELECT 1 FROM ThresholdConfig WHERE ThresholdName = 'IF_Anomaly_Medium');

INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, IsActive)
SELECT 'IF_Anomaly_Low', 'isolation_forest', 0.45, 0.1, 0.7, 'Low risk threshold for Isolation Forest', 1
WHERE NOT EXISTS (SELECT 1 FROM ThresholdConfig WHERE ThresholdName = 'IF_Anomaly_Low');

INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, IsActive)
SELECT 'Confidence_AllAgree', 'confidence', 0.95, 0.8, 1.0, 'Confidence when all models agree', 1
WHERE NOT EXISTS (SELECT 1 FROM ThresholdConfig WHERE ThresholdName = 'Confidence_AllAgree');

INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, IsActive)
SELECT 'Confidence_TwoAgree', 'confidence', 0.75, 0.6, 0.9, 'Confidence when two models agree', 1
WHERE NOT EXISTS (SELECT 1 FROM ThresholdConfig WHERE ThresholdName = 'Confidence_TwoAgree');

INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, IsActive)
SELECT 'Confidence_OneAgrees', 'confidence', 0.50, 0.3, 0.7, 'Confidence when one model agrees', 1
WHERE NOT EXISTS (SELECT 1 FROM ThresholdConfig WHERE ThresholdName = 'Confidence_OneAgrees');

INSERT INTO ThresholdConfig (ThresholdName, ThresholdType, ThresholdValue, MinValue, MaxValue, Description, IsActive)
SELECT 'Confidence_HighRiskBoost', 'confidence', 0.15, 0.0, 0.3, 'Confidence boost for high risk scores', 1
WHERE NOT EXISTS (SELECT 1 FROM ThresholdConfig WHERE ThresholdName = 'Confidence_HighRiskBoost');

-- Verify all thresholds are now present
SELECT ThresholdName, ThresholdValue FROM ThresholdConfig 
WHERE ThresholdName IN (
    'IF_Anomaly_High',
    'IF_Anomaly_Medium', 
    'IF_Anomaly_Low',
    'Confidence_AllAgree',
    'Confidence_TwoAgree',
    'Confidence_OneAgrees',
    'Confidence_HighRiskBoost'
)
ORDER BY ThresholdName;
