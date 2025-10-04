import React, { useState } from 'react';
import ExecutionTraceGraph from './ExecutionTraceGraph';
import MarkdownRenderer from './MarkdownRenderer';

export default function FunctionExecutor({ functionData, onWalkthrough, onClose }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleWalkthrough = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const walkthroughResult = await onWalkthrough(functionData.name, functionData.code, functionData.file);
      setResult(walkthroughResult);
    } catch (err) {
      console.error('Walkthrough error:', err);
      setError(err.message || 'Walkthrough generation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
          <div className="p-6 border-b flex justify-between items-center bg-gray-50">
            <div>
              <h2 className="text-xl font-medium text-gray-900">Function Analysis</h2>
              <p className="text-sm text-gray-600 mt-2">
                <code className="bg-white px-2 py-1 rounded border border-gray-300 text-gray-900 font-mono">{functionData.name}</code>
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-3xl leading-none font-light"
            >
              ×
            </button>
          </div>

          {/* Function Code Display */}
          <div className="p-4 border-b bg-gray-50">
            <h3 className="font-semibold mb-2 text-gray-700">Function Code:</h3>
            <pre className="bg-white p-3 rounded border text-sm overflow-x-auto font-mono text-gray-800 leading-relaxed">
              <code>{functionData.code || 'Code not available'}</code>
            </pre>
          </div>

        {/* Action Button */}
        <div className="p-4 border-b">
          <button
            onClick={handleWalkthrough}
            disabled={loading || !functionData.code}
            className="w-full px-4 py-3 bg-gray-900 text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Analyzing...
              </span>
            ) : (
              <span className="flex items-center justify-center">
                Generate Code Walkthrough
              </span>
            )}
          </button>
          
          <div className="mt-3 text-xs text-gray-500 text-center">
            <p>AI will analyze this function and explain its execution step-by-step with a visual trace graph</p>
          </div>
        </div>

        {/* Walkthrough Results */}
        {result && result.success && (
          <div className="p-4 space-y-4">
            {result.args && Object.keys(result.args).length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-300">
                <h3 className="font-semibold text-gray-900 mb-3">Generated Arguments</h3>
                <pre className="bg-white p-3 rounded border border-gray-200 text-sm overflow-x-auto font-mono text-gray-800">
                  {JSON.stringify(result.args, null, 2)}
                </pre>
              </div>
            )}

            {result.walkthrough && (
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-300">
                <div className="flex items-center mb-3">
                  <h3 className="font-semibold text-gray-900">Code Walkthrough</h3>
                </div>
                <div className="bg-white p-4 rounded border border-gray-200">
                  <MarkdownRenderer content={result.walkthrough} />
                </div>
              </div>
            )}

            {result.trace_graph && (
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-300">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">Execution Flow Diagram</h3>
                  <div className="text-xs bg-white px-3 py-1 rounded border border-gray-300 text-gray-600">
                    Read from top to bottom
                  </div>
                </div>
                <div className="bg-white rounded border border-gray-200">
                  <ExecutionTraceGraph traceData={result.trace_graph} />
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded bg-green-500 mr-1"></div>
                    <span>Start/Return</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded bg-purple-500 mr-1"></div>
                    <span>Assignment</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded bg-amber-500 mr-1"></div>
                    <span>Decision</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded bg-pink-500 mr-1"></div>
                    <span>Loop</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded bg-cyan-500 mr-1"></div>
                    <span>Function Call</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded bg-indigo-500 mr-1"></div>
                    <span>Operation</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {result && !result.success && (
          <div className="p-4">
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="flex items-center mb-2">
                <span className="text-2xl mr-2">❌</span>
                <h3 className="font-semibold text-red-900">Analysis Failed:</h3>
              </div>
              <p className="text-red-700 bg-white p-3 rounded font-mono text-sm">{result.error}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4">
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <div className="flex items-center mb-2">
                <span className="text-2xl mr-2">⚠️</span>
                <h3 className="font-semibold text-red-900">Error:</h3>
              </div>
              <p className="text-red-700 bg-white p-3 rounded">{error}</p>
            </div>
          </div>
        )}

        {/* Close Button */}
        <div className="p-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-semibold"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

