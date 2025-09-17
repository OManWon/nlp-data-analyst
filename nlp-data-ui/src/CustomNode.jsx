import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

// memo를 사용하여 불필요한 재렌더링을 방지합니다.
const CustomNode = memo(({ data, isConnectable }) => {
  return (
    <>
      {/* 노드의 양쪽에 연결 포인트를 만듭니다. */}
      <Handle type="target" position={Position.Left} isConnectable={isConnectable} />
      {/* 노드에 표시될 라벨(이름) */}
      <div>{data.label}</div>
      {/* ✨ 여기가 핵심! 삭제 버튼 추가 ✨ */}
      <button className="delete-btn" onClick={data.onDelete}>
        ×
      </button>
      <Handle type="source" position={Position.Right} isConnectable={isConnectable} />
    </>
  );
});

export default CustomNode;