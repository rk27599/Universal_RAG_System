/**
 * Model Settings Component - AI Model Configuration
 * Manages Ollama model selection, parameters, and system monitoring
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Switch,
  FormControlLabel,
  Alert,
  Chip,
  Paper,
  Divider,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  SmartToy as ModelIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useChat } from '../../contexts/ChatContext';
import apiService from '../../services/api';

interface ModelInfo {
  name: string;
  size: string;
  parameters: string;
  family: string;
  format: string;
  modified_at: string;
}

interface SystemStatus {
  ollama: {
    status: string;
    models: string[];
    version?: string;
  };
  database: {
    status: string;
    connections: number;
  };
  security: {
    score: number;
    violations: number;
  };
}

const ModelSettings: React.FC = () => {
  const {
    availableModels,
    selectedModel,
    setSelectedModel,
    refreshModels,
    isConnected,
  } = useChat();

  const [modelInfos, setModelInfos] = useState<Record<string, ModelInfo>>({});
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Model parameters
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [topP, setTopP] = useState(0.9);
  const [repeatPenalty, setRepeatPenalty] = useState(1.1);
  const [useRAGByDefault, setUseRAGByDefault] = useState(true);
  const [streamingEnabled, setStreamingEnabled] = useState(true);

  // Load system status and model information
  const loadSystemStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.getSystemStatus();
      if (response.success) {
        setSystemStatus(response.data);

        // Load detailed model information
        const modelInfoPromises = response.data.ollama.models.map(async (modelName) => {
          try {
            const modelResponse = await apiService.getModelInfo(modelName);
            return { name: modelName, info: modelResponse.data };
          } catch (err) {
            return { name: modelName, info: null };
          }
        });

        const modelInfoResults = await Promise.all(modelInfoPromises);
        const modelInfoMap: Record<string, ModelInfo> = {};

        modelInfoResults.forEach(({ name, info }) => {
          if (info) {
            modelInfoMap[name] = info;
          }
        });

        setModelInfos(modelInfoMap);
      } else {
        setError(response.message || 'Failed to load system status');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load system status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSystemStatus();
  }, []);

  const handleRefreshModels = async () => {
    await refreshModels();
    await loadSystemStatus();
  };

  const handleModelChange = (newModel: string) => {
    setSelectedModel(newModel);
    // Save to user settings
    // apiService.updateUserSettings({ defaultModel: newModel });
  };

  const formatModelSize = (size: string): string => {
    const sizeInBytes = parseInt(size);
    if (sizeInBytes > 1024 * 1024 * 1024) {
      return `${(sizeInBytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
    } else {
      return `${(sizeInBytes / (1024 * 1024)).toFixed(0)} MB`;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'connected':
      case 'running':
        return <CheckIcon color="success" />;
      case 'error':
      case 'failed':
      case 'disconnected':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSecurityScoreColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    return 'error';
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Model Settings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure AI models and system parameters
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefreshModels}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3, mb: 3 }}>
        {/* System Status */}
        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>

              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress />
                </Box>
              ) : systemStatus ? (
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Ollama Service"
                      secondary={`${systemStatus.ollama.models.length} models available`}
                    />
                    <ListItemSecondaryAction>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getStatusIcon(systemStatus.ollama.status)}
                        <Chip
                          size="small"
                          label={isConnected ? 'Connected' : 'Offline'}
                          color={isConnected ? 'success' : 'error'}
                          variant="outlined"
                        />
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>

                  <ListItem>
                    <ListItemText
                      primary="Database"
                      secondary={`${systemStatus.database.connections} active connections`}
                    />
                    <ListItemSecondaryAction>
                      {getStatusIcon(systemStatus.database.status)}
                    </ListItemSecondaryAction>
                  </ListItem>

                  <ListItem>
                    <ListItemText
                      primary="Security Score"
                      secondary="System security validation"
                    />
                    <ListItemSecondaryAction>
                      <Chip
                        size="small"
                        label={`${systemStatus.security.score}/100`}
                        color={getSecurityScoreColor(systemStatus.security.score)}
                        variant="filled"
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                </List>
              ) : (
                <Typography color="text.secondary">Unable to load system status</Typography>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Model Selection */}
        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Model Selection
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Active Model</InputLabel>
                <Select
                  value={selectedModel}
                  label="Active Model"
                  onChange={(e) => handleModelChange(e.target.value)}
                >
                  {availableModels.map((model) => (
                    <MenuItem key={model} value={model}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <ModelIcon fontSize="small" />
                        {model}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Current Model Info */}
              {modelInfos[selectedModel] && (
                <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Model Information
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Family
                      </Typography>
                      <Typography variant="body2">
                        {modelInfos[selectedModel].family || 'Unknown'}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Size
                      </Typography>
                      <Typography variant="body2">
                        {formatModelSize(modelInfos[selectedModel].size)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Parameters
                      </Typography>
                      <Typography variant="body2">
                        {modelInfos[selectedModel].parameters || 'Unknown'}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Format
                      </Typography>
                      <Typography variant="body2">
                        {modelInfos[selectedModel].format || 'Unknown'}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Model Parameters */}
      <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Model Parameters
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Adjust these settings to control model behavior and response quality
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
                <Box>
                  <Typography gutterBottom>Temperature: {temperature}</Typography>
                  <Slider
                    value={temperature}
                    onChange={(_, value) => setTemperature(value as number)}
                    min={0}
                    max={2}
                    step={0.1}
                    marks={[
                      { value: 0, label: 'Focused' },
                      { value: 1, label: 'Balanced' },
                      { value: 2, label: 'Creative' },
                    ]}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Controls randomness in responses. Lower values are more focused and deterministic.
                  </Typography>
                </Box>

                <Box>
                  <Typography gutterBottom>Max Tokens: {maxTokens}</Typography>
                  <Slider
                    value={maxTokens}
                    onChange={(_, value) => setMaxTokens(value as number)}
                    min={512}
                    max={8192}
                    step={256}
                    marks={[
                      { value: 512, label: '512' },
                      { value: 2048, label: '2K' },
                      { value: 4096, label: '4K' },
                      { value: 8192, label: '8K' },
                    ]}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Maximum length of generated responses.
                  </Typography>
                </Box>

                <Box>
                  <Typography gutterBottom>Top P: {topP}</Typography>
                  <Slider
                    value={topP}
                    onChange={(_, value) => setTopP(value as number)}
                    min={0.1}
                    max={1}
                    step={0.1}
                    marks={[
                      { value: 0.1, label: '0.1' },
                      { value: 0.5, label: '0.5' },
                      { value: 0.9, label: '0.9' },
                    ]}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Controls diversity via nucleus sampling.
                  </Typography>
                </Box>

                <Box>
                  <Typography gutterBottom>Repeat Penalty: {repeatPenalty}</Typography>
                  <Slider
                    value={repeatPenalty}
                    onChange={(_, value) => setRepeatPenalty(value as number)}
                    min={1}
                    max={2}
                    step={0.1}
                    marks={[
                      { value: 1, label: 'None' },
                      { value: 1.1, label: 'Light' },
                      { value: 1.5, label: 'Strong' },
                    ]}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Reduces repetition in responses.
                  </Typography>
                </Box>
              </Box>

              <Divider sx={{ my: 3 }} />

              {/* Advanced Settings */}
              <Typography variant="h6" gutterBottom>
                Advanced Settings
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
                <Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={useRAGByDefault}
                        onChange={(e) => setUseRAGByDefault(e.target.checked)}
                      />
                    }
                    label="Use RAG by default"
                  />
                  <Typography variant="caption" color="text.secondary" display="block">
                    Automatically use document context in responses
                  </Typography>
                </Box>

                <Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={streamingEnabled}
                        onChange={(e) => setStreamingEnabled(e.target.checked)}
                      />
                    }
                    label="Enable streaming"
                  />
                  <Typography variant="caption" color="text.secondary" display="block">
                    Show responses as they are generated
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                <Button variant="contained" color="primary">
                  Save Settings
                </Button>
                <Button variant="outlined">
                  Reset to Defaults
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>

      {/* Security Notice */}
      <Box>
        <Alert severity="info" icon={<CheckIcon />}>
          <Typography variant="subtitle2" gutterBottom>
            🔒 Local Processing Enabled
          </Typography>
          All AI models run locally on your system. No data is sent to external services,
          ensuring complete privacy and data sovereignty.
        </Alert>
      </Box>
    </Box>
  );
};

export default ModelSettings;