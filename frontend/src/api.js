import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const uploadRepository = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(`${API_BASE}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const uploadPaper = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(`${API_BASE}/upload-paper`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const queryCodebase = async (query) => {
  const response = await axios.post(`${API_BASE}/query`, { query });
  return response.data;
};

export const getGraph = async (view = 'features') => {
  const response = await axios.get(`${API_BASE}/graph?view=${view}`);
  return response.data;
};

export const getFeatureDetails = async (featureId) => {
  const response = await axios.get(`${API_BASE}/feature/${featureId}`);
  return response.data;
};

export const walkthroughFunction = async (functionName, functionCode, filePath) => {
  const response = await axios.post(`${API_BASE}/walkthrough-function`, {
    function_name: functionName,
    function_code: functionCode,
    file_path: filePath
  });
  return response.data;
};

export const executeFunction = async (functionName, functionCode, filePath) => {
  const response = await axios.post(`${API_BASE}/execute-function`, {
    function_name: functionName,
    function_code: functionCode,
    file_path: filePath
  });
  return response.data;
};

