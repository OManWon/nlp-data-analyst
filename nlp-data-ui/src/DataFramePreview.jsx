import React from 'react';

function DataFramePreview({ previewData }) {
  // 보여줄 데이터가 없으면 안내 메시지를 표시
  if (!previewData) {
    return <div className="preview-panel-placeholder">노드를 클릭하여 데이터 미리보기를 확인하세요.</div>;
  }

  const { columns, data } = previewData;

  return (
    <div className="preview-panel">
      <h4>데이터 미리보기</h4>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              {columns.map(col => <th key={col}>{col}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default DataFramePreview;