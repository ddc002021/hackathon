import React, { useState } from 'react';

export default function UploadPanel({ onBuildGraph }) {
  const [codeFile, setCodeFile] = useState(null);
  const [paperFile, setPaperFile] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCodeFileChange = (e) => {
    setCodeFile(e.target.files[0]);
  };

  const handlePaperFileChange = (e) => {
    setPaperFile(e.target.files[0]);
  };

  const handleBuildGraph = async () => {
    if (!codeFile || !paperFile) return;
    setLoading(true);
    await onBuildGraph(codeFile, paperFile);
    setLoading(false);
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-light text-gray-900 mb-3 tracking-wide">
          Upload Materials
        </h2>
        <p className="text-gray-700 mb-2">
          Provide a research paper and its corresponding code repository
        </p>
        <p className="text-sm text-gray-600">
          The system will extract sections from the paper and map them to code implementations
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        {/* Code Upload */}
        <div className="bg-white border border-gray-200 shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900">
              Code Repository
            </h3>
          </div>
          <div className="p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select ZIP Archive
            </label>
            <input
              type="file"
              accept=".zip"
              onChange={handleCodeFileChange}
              disabled={loading}
              className="block w-full text-sm text-gray-900 border border-gray-300 cursor-pointer bg-white focus:outline-none file:mr-4 file:py-2 file:px-4 file:border-0 file:text-sm file:font-medium file:bg-gray-900 file:text-white hover:file:bg-gray-800 file:cursor-pointer disabled:opacity-50"
            />
            <p className="mt-2 text-xs text-gray-500">
              Accepted format: .zip
            </p>
            {codeFile && (
              <div className="mt-3 flex items-center gap-2 text-sm text-green-700 bg-green-50 px-3 py-2 border border-green-200">
                <span>✓</span>
                <span className="font-medium">{codeFile.name}</span>
              </div>
            )}
          </div>
        </div>

        {/* Paper Upload */}
        <div className="bg-white border border-gray-200 shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900">
              Research Paper
            </h3>
          </div>
          <div className="p-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Document
            </label>
            <input
              type="file"
              accept=".pdf,.txt"
              onChange={handlePaperFileChange}
              disabled={loading}
              className="block w-full text-sm text-gray-900 border border-gray-300 cursor-pointer bg-white focus:outline-none file:mr-4 file:py-2 file:px-4 file:border-0 file:text-sm file:font-medium file:bg-gray-900 file:text-white hover:file:bg-gray-800 file:cursor-pointer disabled:opacity-50"
            />
            <p className="mt-2 text-xs text-gray-500">
              Accepted formats: .pdf, .txt
            </p>
            {paperFile && (
              <div className="mt-3 flex items-center gap-2 text-sm text-green-700 bg-green-50 px-3 py-2 border border-green-200">
                <span>✓</span>
                <span className="font-medium">{paperFile.name}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Build Graph Button */}
      <div className="mb-12">
        <button
          onClick={handleBuildGraph}
          disabled={!codeFile || !paperFile || loading}
          className="w-full px-6 py-4 bg-gray-900 text-white text-base font-medium hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm border-2 border-gray-900"
        >
          {loading ? 'Building Graph...' : 'Build Graph'}
        </button>
        {(!codeFile || !paperFile) && (
          <p className="mt-3 text-sm text-center text-gray-500">
            Please select both files to build the graph
          </p>
        )}
      </div>

      <div className="bg-blue-50 border-2 border-blue-300 p-6 rounded-lg">
        <div className="flex items-start gap-3">
          <div className="text-2xl">ℹ️</div>
          <div>
            <p className="text-sm font-semibold text-blue-900 mb-2">
              How it works
            </p>
            <p className="text-sm text-blue-800">
              Select both files, then click <strong>"Build Graph"</strong> to process them together. 
              The system will extract implementation-relevant sections from the paper and map them to actual code functions using semantic analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

