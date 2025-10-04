import React from 'react';

export default function PathVisualization({ paths, queryType }) {
  if (!paths || paths.length === 0) return null;

  return (
    <div className="absolute top-4 right-4 bg-white border-2 border-amber-500 rounded-lg shadow-lg max-w-md z-10">
      <div className="px-4 py-3 bg-amber-50 border-b border-amber-200">
        <h3 className="text-sm font-semibold text-amber-900 flex items-center gap-2">
          {queryType === 'path' ? 'Implementation Path' : 'Graph Path'}
          <span className="ml-auto text-xs font-normal text-amber-700">
            {paths.length} path{paths.length > 1 ? 's' : ''} found
          </span>
        </h3>
      </div>
      
      <div className="p-4 max-h-96 overflow-y-auto">
        {paths.map((path, pathIdx) => (
          <div key={pathIdx} className="mb-4 last:mb-0">
            {paths.length > 1 && (
              <div className="text-xs font-semibold text-gray-600 mb-2">
                Path {pathIdx + 1}:
              </div>
            )}
            
            {path.steps && path.steps.length > 0 ? (
              <div className="space-y-3">
                {path.steps.map((step, stepIdx) => (
                  <div key={stepIdx} className="flex items-start gap-2">
                    <div className="flex-shrink-0 mt-1">
                      <div className="w-6 h-6 rounded-full bg-amber-500 text-white text-xs flex items-center justify-center font-bold">
                        {stepIdx + 1}
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-gray-900 truncate">
                          {step.from_name}
                        </span>
                        <span className="flex-shrink-0 text-xs text-amber-600 font-semibold px-2 py-0.5 bg-amber-50 rounded">
                          {step.relation}
                        </span>
                      </div>
                      
                      {step.description && (
                        <p className="text-xs text-gray-600 line-clamp-2">
                          {step.description}
                        </p>
                      )}
                      
                      {stepIdx < path.steps.length - 1 && (
                        <div className="ml-3 mt-2 mb-1 border-l-2 border-amber-300 h-3"></div>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* Final node */}
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-6 h-6 rounded-full bg-green-500 text-white text-xs flex items-center justify-center">
                      ✓
                    </div>
                  </div>
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-900">
                      {path.steps[path.steps.length - 1].to_name}
                    </span>
                  </div>
                </div>
              </div>
            ) : path.nodes ? (
              // Fallback: just show nodes if steps not available
              <div className="flex items-center gap-2 flex-wrap">
                {path.nodes.map((node, idx) => (
                  <React.Fragment key={idx}>
                    <span className="text-xs font-medium text-gray-700 bg-gray-100 px-2 py-1 rounded">
                      {node}
                    </span>
                    {idx < path.nodes.length - 1 && (
                      <span className="text-amber-500 text-sm">→</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
      
      <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-600">
        Orange edges show the path on the graph
      </div>
    </div>
  );
}

