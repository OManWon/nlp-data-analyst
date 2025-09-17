import React, { useEffect, useMemo } from 'react';
import ReactFlow, { MiniMap, Controls, Background } from 'reactflow';
import 'reactflow/dist/style.css';

// 1. 우리가 만든 커스텀 노드를 import 합니다.
import CustomNode from './CustomNode';

function DataChronicle({ nodes, edges, fetchGraphData, invokeAgent, fetchPreviewData  }) {
  
  // 2. React Flow에 어떤 종류의 커스텀 노드가 있는지 알려줍니다.
  const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  const onNodeClick = (event, node) => {
    // 1. 활성 DF로 설정하는 명령을 에이전트에게 보냄
    const prompt = `${node.id}를 활성 데이터로 설정해줘.`;
    invokeAgent(prompt);
    
    // ✨ 2. 동시에 해당 노드의 미리보기 데이터를 요청함
    fetchPreviewData(node.id);
  };

  // 3. 삭제 버튼 클릭 시 실행될 함수를 정의합니다.
  const createDeleteHandler = (nodeId) => (event) => {
    // 이벤트 버블링을 막아 노드 클릭 이벤트가 함께 실행되는 것을 방지합니다.
    event.stopPropagation(); 
    const prompt = `delete_dataframe('${nodeId}')`;
    invokeAgent(prompt);
  };
  
  // 4. 노드 데이터에 onDelete 함수를 추가합니다.
  const nodesWithHandlers = nodes.map(node => ({
    ...node,
    type: 'custom', // 모든 노드 타입을 'custom'으로 지정
    data: { 
      ...node.data,
      onDelete: createDeleteHandler(node.id) 
    }
  }));

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
          nodes={nodesWithHandlers}
          edges={edges}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes} // 커스텀 노드 타입을 등록합니다.
          fitView
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}

export default DataChronicle;