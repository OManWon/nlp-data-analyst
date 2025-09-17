import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

// ✨ Base64 데이터를 파일로 다운로드하는 함수
const saveAsFile = (base64Data, filename) => {
  const link = document.createElement('a');
  link.href = `data:image/png;base64,${base64Data}`;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

function PlotsGallery() {
  const [plots, setPlots] = useState([]);

  useEffect(() => {
    // 컴포넌트가 로드될 때 저장된 플롯 목록을 가져옵니다.
    axios.get(`${API_URL}/api/project/plots`)
      .then(response => {
        setPlots(response.data);
      })
      .catch(error => console.error("플롯 데이터를 가져오는 데 실패했습니다:", error));
  }, []);

  if (plots.length === 0) {
    return <div className="plots-gallery-empty">생성된 플롯이 없습니다.</div>;
  }

  return (
    <div className="plots-gallery">
      {plots.map(plot => (
        <div key={plot.id} className="plot-item" onClick={() => saveAsFile(plot.image_base64, `${plot.id}.png`)}>
          <img src={`data:image/png;base64,${plot.image_base64}`} alt={`Plot ${plot.id}`} />
          <div className="plot-overlay">저장하기</div>
        </div>
      ))}
    </div>
  );
}

export default PlotsGallery;