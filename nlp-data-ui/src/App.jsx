import React, { useState, useCallback } from 'react';
import axios from 'axios';
import DataChronicle from './DataChronicle'; // 그래프 컴포넌트
import ChatUI from './ChatUI'; // 새로 만들 채팅 컴포넌트
import PlotsGallery from './PlotsGallery';
import DataFramePreview from './DataFramePreview';
import './App.css';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [chatHistory, setChatHistory] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [activeTab, setActiveTab] = useState('chat');
  const [previewData, setPreviewData] = useState(null);

  // 데이터 연대기 상태를 가져오는 함수
  const fetchGraphData = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/project/state`);
      const data = response.data;

      // --- ✨ 바로 이 부분이 수정되었습니다! ---
      // API 응답을 React Flow가 이해하는 형식으로 변환합니다.
      const flowNodes = data.nodes.map((node, index) => ({
        id: node.id,
        data: { label: node.label },
        // 각 노드의 위치(position)를 자동으로 계산하여 할당합니다.
        position: { x: (index % 4) * 250, y: Math.floor(index / 4) * 150 },
        // 활성 노드를 강조하는 스타일입니다.
        style: node.id === data.active_node_id 
            ? { border: '3px solid #ff0072', boxShadow: '0 0 10px #ff0072' } 
            : {},
      }));

      const flowEdges = data.edges.map(edge => ({
        id: `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        animated: edge.target === data.active_node_id,
      }));
      // --- ✨ 여기까지가 수정된 부분입니다. ---

      setNodes(flowNodes);
      setEdges(flowEdges);

    } catch (error) {
      console.error("그래프 데이터를 가져오는 데 실패했습니다:", error);
    }
  }, []);
  const fetchPreviewData = async (nodeId) => {
    try {
      const response = await axios.get(`${API_URL}/api/dataframe/${nodeId}/preview`);
      setPreviewData(response.data);
    } catch (error) {
      console.error("미리보기 데이터를 가져오는 데 실패했습니다:", error);
      setPreviewData(null);
    }
  };

  // 에이전트를 호출하는 함수
  const invokeAgent = async (prompt) => {
    if (!prompt) return;

    // 사용자 메시지 대신 시스템 메시지로 처리할 수도 있습니다.
    // 여기서는 간단하게 사용자 메시지처럼 추가합니다.
    setChatHistory(prev => [...prev, { sender: 'user', content: prompt }]);

    try {
      const response = await axios.post(`${API_URL}/api/agent/invoke`, { input: prompt });
      setChatHistory(prev => [...prev, { sender: 'agent', content: response.data }]);
      fetchGraphData(); 
    } catch (error) {
      console.error("에이전트 호출에 실패했습니다:", error);
      setChatHistory(prev => [...prev, { sender: 'agent', content: { final_answer: "오류가 발생했습니다." } }]);
    }
  };

  return (
    <div className="app-container">
      <div className="tab-content">
          {activeTab === 'chat' && (
            <div className="chat-view">
              <div className="graph-panel">
                {/* ✨ 4. fetchPreviewData 함수를 props로 전달 */}
                <DataChronicle 
                  nodes={nodes} 
                  edges={edges} 
                  fetchGraphData={fetchGraphData} 
                  invokeAgent={invokeAgent} 
                  fetchPreviewData={fetchPreviewData} 
                />
              </div>
              <div className="chat-panel">
                <DataFramePreview previewData={previewData} />
                <ChatUI 
                  chatHistory={chatHistory} 
                  invokeAgent={invokeAgent} 
                  fetchGraphData={fetchGraphData} // ✨ props로 전달
                />
              </div>
            </div>
          )}
          {activeTab === 'plots' && <PlotsGallery />}
        </div>
    </div>
  );
}

export default App;