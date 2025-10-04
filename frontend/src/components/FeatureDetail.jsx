import React, { useState } from 'react';
import FunctionExecutor from './FunctionExecutor';

export default function FeatureDetail({ feature, onClose, onWalkthroughFunction }) {
  const [selectedFunction, setSelectedFunction] = useState(null);
  const isPaper = feature.modality === 'paper';

  const handleFunctionClick = (func) => {
    setSelectedFunction(func);
  };

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-40">
        <div className="bg-white shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto border border-gray-300">
          {/* Header */}
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <div className="flex justify-between items-start">
              <div>
                <div className="mb-3">
                  <span className={`px-3 py-1 text-xs font-medium border ${
                    isPaper ? 'bg-orange-50 border-orange-400 text-orange-800' : 'bg-purple-50 border-purple-400 text-purple-800'
                  }`}>
                    {isPaper ? 
                      (feature.type === 'paper_section' ? 'PAPER SECTION' :
                       feature.type === 'paper_algorithm' ? 'ALGORITHM' :
                       feature.type === 'concept' ? 'CONCEPT' :
                       feature.type === 'component' ? 'COMPONENT' :
                       feature.type === 'technique' ? 'TECHNIQUE' :
                       'PAPER NODE')
                      : 'CODE IMPLEMENTATION'}
                  </span>
                </div>
                <h2 className="text-2xl font-light text-gray-900 mb-2">{feature.name}</h2>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{feature.description}</p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-3xl leading-none font-light"
              >
                ×
              </button>
            </div>
          </div>

          {/* Paper Full Content */}
          {isPaper && feature.full_content && (
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-base font-medium text-gray-900 mb-3">
                Section Content
              </h3>
              <div className="bg-gray-50 border border-gray-200 p-5 max-h-[500px] overflow-y-auto">
                <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">{feature.full_content}</p>
              </div>
              <p className="text-xs text-gray-500 mt-2 italic">
                This section from the research paper is mapped to code implementations shown in the graph
              </p>
            </div>
          )}

          {/* Files Section (only for code) */}
          {!isPaper && feature.files && feature.files.length > 0 && (
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-base font-medium text-gray-900 mb-3">
                Related Files ({feature.files.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {feature.files.map((file, idx) => (
                  <div key={idx} className="bg-gray-50 px-3 py-2 border border-gray-200">
                    <code className="text-xs text-gray-800 font-mono">{file}</code>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Functions Section (only for code) */}
          {!isPaper && (
            <div className="p-6">
              <h3 className="text-base font-medium text-gray-900 mb-3">
                Functions ({feature.functions?.length || 0})
              </h3>
              {!feature.functions || feature.functions.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8">No functions available</p>
              ) : (
                <div className="space-y-3">
                  {feature.functions.map((func, idx) => (
                    <div
                      key={idx}
                      className="bg-white border border-gray-200 p-4 hover:border-gray-400 cursor-pointer transition-colors"
                      onClick={() => handleFunctionClick(func)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <code className="text-sm text-gray-900 font-mono font-medium">{func.name}()</code>
                          <p className="text-xs text-gray-500 mt-2">
                            {func.file} <span className="text-gray-400">· Line {func.lineno}</span>
                          </p>
                        </div>
                        <button className="ml-4 px-4 py-2 bg-gray-900 text-white text-xs font-medium hover:bg-gray-800 transition-colors">
                          Analyze
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Close Button */}
          <div className="p-6 border-t border-gray-200 bg-gray-50">
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Function Executor Modal */}
      {selectedFunction && (
        <FunctionExecutor
          functionData={selectedFunction}
          onWalkthrough={onWalkthroughFunction}
          onClose={() => setSelectedFunction(null)}
        />
      )}
    </>
  );
}

