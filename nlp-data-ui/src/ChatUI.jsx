import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
const API_URL = 'http://127.0.0.1:8000';

function ChatUI({ chatHistory, invokeAgent, fetchGraphData  }) {
  const [userInput, setUserInput] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const chatEndRef = useRef(null);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  // ✨ 파일 업로드 핸들러
  const handleUpload = async () => {
    if (!selectedFile) {
      alert("먼저 파일을 선택해주세요.");
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      alert(response.data.message || "업로드 성공!");
      setSelectedFile(null); // 파일 선택 초기화
      document.getElementById('file-input').value = null; // input 값 초기화
      fetchGraphData(); // ✨ 업로드 성공 후 그래프 갱신!
    } catch (error) {
      console.error("파일 업로드에 실패했습니다:", error);
      alert("파일 업로드에 실패했습니다.");
    }
  };

  // 채팅이 업데이트될 때마다 맨 아래로 스크롤
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const handleSubmit = (event) => {
    event.preventDefault();
    invokeAgent(userInput);
    setUserInput('');
  };

  return (
    <div className="chat-container">
      <div className="file-upload-section">
        <input type="file" id="file-input" onChange={handleFileChange} accept=".csv" />
        {selectedFile && <span className="file-name">{selectedFile.name}</span>}
        <button onClick={handleUpload} disabled={!selectedFile}>업로드</button>
      </div>
      <div className="chat-log">
        {chatHistory.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.sender}`}>
            {msg.sender === 'user' ? (
                <p>{msg.content}</p>
            ) : (
                <div>
                {/* ✨ 여기가 핵심! ✨ */}
                {/* 최종 답변이 객체이고, 그 안에 텍스트 결과가 있다면 표시 */}
                {typeof msg.content.final_answer === 'object' && msg.content.final_answer.text_result && (
                    <p><b>답변:</b> {msg.content.final_answer.text_result}</p>
                )}

                {/* 최종 답변이 단순 문자열이면 그대로 표시 (오류 메시지 등) */}
                {typeof msg.content.final_answer === 'string' && (
                    <p><b>답변:</b> {msg.content.final_answer}</p>
                )}

                {/* 최종 답변에 Base64 이미지 데이터가 있다면, 이미지로 렌더링 */}
                {typeof msg.content.final_answer === 'object' && msg.content.final_answer.image_base64 && (
                    <img 
                    src={`data:image/png;base64,${msg.content.final_answer.image_base64}`} 
                    alt="Generated Plot" 
                    style={{ maxWidth: '100%', borderRadius: '8px', marginTop: '10px' }}
                    />
                )}
                
                {/* 생각 보기 부분은 이전과 동일 */}
                {msg.content.thoughts && msg.content.thoughts.length > 0 && (
                    <details className="thought-process">
                    {/* ... */}
                    </details>
                )}
                </div>
            )}
            </div>
        ))}
        <div ref={chatEndRef} />
        </div>
      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder="데이터에게 말을 걸어보세요..."
        />
        <button type="submit">전송</button>
      </form>
    </div>
  );
}

export default ChatUI;