import React, { useState } from 'react';
import GraphView from './components/GraphView';
import ChatInterface from './components/ChatInterface';
import UploadPanel from './components/UploadPanel';
import FeatureDetail from './components/FeatureDetail';
import { uploadRepository, uploadPaper, queryCodebase, walkthroughFunction, getFeatureDetails } from './api';

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [messages, setMessages] = useState([]);
  const [highlightedNodes, setHighlightedNodes] = useState([]);
  const [highlightedPaths, setHighlightedPaths] = useState([]);  // NEW: Store paths for visualization
  const [queryType, setQueryType] = useState(null);  // NEW: Store query type
  const [graphLoaded, setGraphLoaded] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState(null);
  const [hasPaper, setHasPaper] = useState(false);
  const [hasCode, setHasCode] = useState(false);

  const handleBuildGraph = async (codeFile, paperFile) => {
    try {
      // Upload code first
      setMessages([
        { role: 'assistant', content: 'Uploading and parsing code repository...' }
      ]);
      
      const codeData = await uploadRepository(codeFile);
      console.log('Code upload response:', codeData);
      setHasCode(true);
      
      // Then upload paper (which will trigger cross-modal mapping)
      setMessages([
        { role: 'assistant', content: 'Parsing research paper and creating semantic mappings...' }
      ]);
      
      const paperData = await uploadPaper(paperFile);
      console.log('Paper upload response:', paperData);
      setHasPaper(true);
      
      // Paper upload should return the cross-modal graph
      if (paperData.nodes && paperData.edges) {
        console.log(`Cross-modal graph created: ${paperData.nodes.length} nodes, ${paperData.edges.length} edges`);
        console.log('   Paper nodes:', paperData.nodes.filter(n => n.data.modality === 'paper').length);
        console.log('   Code nodes:', paperData.nodes.filter(n => n.data.modality === 'code').length);
        
        setGraphData({ nodes: paperData.nodes, edges: paperData.edges });
        setGraphLoaded(true);
        
        const paperCount = paperData.nodes.filter(n => n.data.modality === 'paper').length;
        const codeCount = paperData.nodes.filter(n => n.data.modality === 'code').length;
        
        setMessages([
          { role: 'assistant', content: `Cross-modal graph built successfully! The graph shows ${paperCount} paper sections (orange, left) semantically mapped to ${codeCount} code functions (purple, right). Click any node to explore details, or use the chat to query the codebase.` }
        ]);
      } else {
        throw new Error('Failed to build cross-modal graph');
      }
    } catch (error) {
      console.error('Build graph failed:', error);
      alert('Failed to build graph. Please check your files and try again.');
      setMessages([
        { role: 'assistant', content: 'Failed to build graph. Please try again.' }
      ]);
    }
  };

  const handleQuery = async (query) => {
    setMessages((prev) => [...prev, { role: 'user', content: query }]);
    
    // Clear previous highlights immediately
    setHighlightedNodes([]);
    setHighlightedPaths([]);

    try {
      const response = await queryCodebase(query);
      
      // Build assistant message with query type indicator
      let assistantMessage = response.answer;
      if (response.query_type) {
        assistantMessage = `**${response.query_type.toUpperCase()} QUERY**\n\n${assistantMessage}`;
      }
      
      setMessages((prev) => [...prev, { role: 'assistant', content: assistantMessage }]);
      
      // Set new highlights after a small delay to ensure clear happens first
      setTimeout(() => {
        setHighlightedNodes(response.highlighted_nodes || []);
        setHighlightedPaths(response.paths || []);
        setQueryType(response.query_type);
        
        // Log path info for debugging
        if (response.paths && response.paths.length > 0) {
          console.log('Paths found:', response.paths);
          response.paths.forEach((path, idx) => {
            console.log(`  Path ${idx + 1}:`, path.nodes?.join(' → '));
          });
        }
      }, 50);
    } catch (error) {
      console.error('Query failed:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error processing your query.' }
      ]);
      setHighlightedNodes([]);
      setHighlightedPaths([]);
    }
  };

  const handleFeatureClick = async (featureId) => {
    // Prevent multiple rapid clicks
    if (selectedFeature) {
      return;
    }
    
    try {
      const details = await getFeatureDetails(featureId);
      setSelectedFeature(details);
    } catch (error) {
      console.error('Failed to fetch feature details:', error);
      alert('Failed to load feature details');
    }
  };

  const handleWalkthroughFunction = async (functionName, functionCode, filePath) => {
    try {
      const result = await walkthroughFunction(functionName, functionCode, filePath);
      return result;
    } catch (error) {
      console.error('Walkthrough generation failed:', error);
      throw error;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Professional Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            {/* Left: AUB Logo + Title */}
            <div className="flex items-center gap-6">
              <img 
                src="/AUBlogo.png" 
                alt="American University of Beirut" 
                className="h-48 w-48 object-contain"
              />
              <div className="border-l-2 border-gray-300 pl-6">
                <h1 className="text-2xl font-light text-gray-900 tracking-wide">
                  Paper–Code Mapper
                </h1>
                <p className="text-sm text-gray-500 mt-1">Cross-Modal Graph Representation Learning</p>
              </div>
            </div>
            
            {/* Right: Student Info */}
            <div className="text-right border-l-2 border-gray-300 pl-6">
              <p className="text-sm font-medium text-gray-900">Dany Chahine</p>
              <p className="text-xs text-gray-600 mt-1">Student ID: 202107582</p>
              <p className="text-xs text-gray-600">EECE 798S</p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-8 py-8">
        {!graphLoaded ? (
          <div className="mt-12">
            <UploadPanel onBuildGraph={handleBuildGraph} />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Graph View Card */}
            <div className="bg-white border border-gray-200 shadow-sm">
              <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h2 className="text-lg font-medium text-gray-900">
                  Graph Visualization
                </h2>
              </div>
              <GraphView
                initialNodes={graphData.nodes}
                initialEdges={graphData.edges}
                highlightedNodes={highlightedNodes}
                highlightedPaths={highlightedPaths}
                onFeatureClick={handleFeatureClick}
              />
            </div>

            {/* Chat Interface Card */}
            <div className="bg-white border border-gray-200 shadow-sm" style={{ height: '700px' }}>
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h2 className="text-lg font-medium text-gray-900">
                  Query Interface
                </h2>
              </div>
              <div style={{ height: 'calc(100% - 65px)' }}>
                <ChatInterface onQuery={handleQuery} messages={messages} />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Feature Detail Modal */}
      {selectedFeature && (
        <FeatureDetail
          feature={selectedFeature}
          onClose={() => setSelectedFeature(null)}
          onWalkthroughFunction={handleWalkthroughFunction}
        />
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16 py-8">
        <div className="container mx-auto px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img 
                src="/AUBlogo.png" 
                alt="AUB Logo" 
                className="h-32 w-32 object-contain opacity-90"
              />
              <div className="text-sm text-gray-600">
                <p className="font-medium text-gray-900">American University of Beirut</p>
              </div>
            </div>
            <div className="text-right text-sm text-gray-600">
              <p>EECE 798S</p>
              <p className="text-xs mt-1">Dany Chahine (202107582)</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

