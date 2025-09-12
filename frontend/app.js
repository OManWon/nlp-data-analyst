document.addEventListener('DOMContentLoaded', () => {
    // --- 상태 관리 ---
    const state = {
        projects: [],
        currentProjectId: null,
        datasets: [],
        chatHistory: [],
    };

    // --- API 서비스 ---
    const api = {
        BASE_URL: '/api',
        async getProjects() {
            const response = await fetch(`${this.BASE_URL}/project/list`);
            if (!response.ok) throw new Error('Failed to fetch projects.');
            return response.json();
        },
        async createProject(name) {
            const response = await fetch(`${this.BASE_URL}/project/new?name=${encodeURIComponent(name)}`, { method: 'POST' });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to create project.');
            }
            return response.json();
        },
        async deleteProject(name) {
            const response = await fetch(`${this.BASE_URL}/project/delete?name=${encodeURIComponent(name)}`, { method: 'DELETE' });
            if (!response.ok) throw new Error('Failed to delete project.');
            return response.json();
        },
        async getDatasets(projectId) {
            const response = await fetch(`${this.BASE_URL}/project/${projectId}/data`);
            if (!response.ok) throw new Error('Failed to fetch datasets.');
            return response.json();
        },
        async uploadFile(projectId, file) {
            const formData = new FormData();
            formData.append('file', file);
            const response = await fetch(`${this.BASE_URL}/project/${projectId}/upload`, {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) throw new Error('File upload failed.');
            return response.json();
        },
        async getChatHistory(projectId) {
            const response = await fetch(`${this.BASE_URL}/project/${projectId}/chat/history`);
            if (!response.ok) throw new Error('Failed to fetch chat history.');
            return response.json();
        },
        async postChat(projectId, query, chatHistory) {
            const response = await fetch(`${this.BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: projectId, q: query, chat_history: chatHistory }),
            });
            if (!response.ok) throw new Error('Chat request failed.');
            return response.json();
        },
    };

    // --- UI 요소 ---
    const ui = {
        projectList: document.getElementById('project-list'),
        datasetList: document.getElementById('dataset-list'),
        chatMessages: document.getElementById('chat-messages'),
        messageInput: document.getElementById('message-input'),
        sendButton: document.getElementById('send-button'),
        chatForm: document.getElementById('chat-form'),
        welcomeScreen: document.getElementById('welcome-screen'),
        chatContainer: document.getElementById('chat-container'),
        currentProjectDetails: document.getElementById('current-project-details'),
        newProjectModal: new bootstrap.Modal(document.getElementById('newProjectModal')),
        createProjectBtn: document.getElementById('create-project-btn'),
        newProjectForm: document.getElementById('new-project-form'),
        projectNameInput: document.getElementById('project-name-input'),
        fileUploadInput: document.getElementById('file-upload-input'),
    };
    
    const converter = new showdown.Converter();

    // --- 렌더링 함수 ---
    function renderProjects() {
        ui.projectList.innerHTML = '';
        state.projects.forEach(p => {
            const li = document.createElement('li');
            li.className = 'nav-item';
            li.innerHTML = `
                <a class="nav-link d-flex justify-content-between align-items-center ${p.experiment_id === state.currentProjectId ? 'active' : ''}" href="#" data-id="${p.experiment_id}">
                    ${p.name}
                    <button class="btn btn-sm btn-outline-danger delete-project-btn" data-name="${p.name}"><i class="bi bi-trash"></i></button>
                </a>
            `;
            ui.projectList.appendChild(li);
        });
    }

    function renderDatasets() {
        ui.datasetList.innerHTML = '';
        state.datasets.forEach(d => {
            const li = document.createElement('li');
            li.className = 'nav-item';
            li.innerHTML = `<span class="nav-link text-muted small">${d.path.split('/').pop()}</span>`;
            ui.datasetList.appendChild(li);
        });
        if(state.datasets.length > 0) {
            ui.messageInput.disabled = false;
            ui.sendButton.disabled = false;
        }
    }

    function renderChatMessage(message) {
        const div = document.createElement('div');
        div.className = `chat-message ${message.role}`;
        let content = '';
        if (message.role === 'user') {
            content = `<p>${message.content}</p>`;
        } else { // assistant
            const planHtml = converter.makeHtml(message.plan);
            const codeBlock = message.code ? `<h6>Generated Code:</h6><pre><code>${message.code}</code></pre>` : '';
            const stdoutBlock = message.stdout ? `<h6>Stdout:</h6><pre>${message.stdout}</pre>` : '';
            const stderrBlock = message.stderr ? `<h6>Stderr:</h6><pre class="text-danger">${message.stderr}</pre>` : '';
            const errorBlock = message.error ? `<h6>Error:</h6><pre class="text-danger">${message.error}</pre>` : '';
            
            let artifactsBlock = '<h6>Artifacts:</h6>';
            if(message.artifacts && message.artifacts.length > 0) {
                 message.artifacts.forEach(a => {
                    if(a.type === 'plot') {
                        const plotUrl = `/mlruns/${state.currentProjectId}/${message.run_id}/artifacts/${a.path}?t=${new Date().getTime()}`;
                        artifactsBlock += `<img src="${plotUrl}" class="img-fluid mt-2" alt="plot">`;
                    }
                });
            } else {
                artifactsBlock += '<p>No artifacts generated.</p>';
            }

            content = `${planHtml}${codeBlock}${stdoutBlock}${stderrBlock}${errorBlock}${artifactsBlock}`;
        }
        div.innerHTML = content;
        ui.chatMessages.appendChild(div);
        ui.chatMessages.scrollTop = ui.chatMessages.scrollHeight;
    }

    function renderChatHistory() {
        ui.chatMessages.innerHTML = '';
        state.chatHistory.forEach(renderChatMessage);
    }

    // --- 이벤트 핸들러 ---
    async function handleLoadProjects() {
        try {
            state.projects = await api.getProjects();
            renderProjects();
        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    }

    async function handleSelectProject(e) {
        if (e.target.closest('.delete-project-btn')) return;
        const link = e.target.closest('a');
        if (!link) return;

        state.currentProjectId = link.dataset.id;
        ui.welcomeScreen.classList.add('d-none');
        ui.chatContainer.classList.remove('d-none');
        ui.currentProjectDetails.classList.remove('d-none');
        renderProjects();
        await handleLoadDatasets();
        await handleLoadChatHistory();
    }
    
    async function handleLoadChatHistory() {
        if (!state.currentProjectId) return;
        try {
            state.chatHistory = await api.getChatHistory(state.currentProjectId);
            renderChatHistory();
        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    }

    async function handleCreateProject() {
        const name = ui.projectNameInput.value.trim();
        if (!name) return;

        try {
            await api.createProject(name);
            ui.newProjectModal.hide();
            ui.newProjectForm.reset();
            await handleLoadProjects();
        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    }
    
    async function handleDeleteProject(e) {
        const button = e.target.closest('.delete-project-btn');
        if (!button) return;

        const projectName = button.dataset.name;
        if (confirm(`정말로 '${projectName}' 프로젝트를 삭제하시겠습니까?`)) {
            try {
                await api.deleteProject(projectName);
                await handleLoadProjects();
                if(state.currentProjectId && state.projects.every(p => p.experiment_id !== state.currentProjectId)) {
                    state.currentProjectId = null;
                    ui.welcomeScreen.classList.remove('d-none');
                    ui.chatContainer.classList.add('d-none');
                    ui.currentProjectDetails.classList.add('d-none');
                }
            } catch (error) {
                console.error(error);
                alert(error.message);
            }
        }
    }

    async function handleLoadDatasets() {
        if (!state.currentProjectId) return;
        try {
            const data = await api.getDatasets(state.currentProjectId);
            state.datasets = data.datasets || [];
            renderDatasets();
        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    }

    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file || !state.currentProjectId) return;

        try {
            await api.uploadFile(state.currentProjectId, file);
            await handleLoadDatasets();
        } catch (error) {
            console.error(error);
            alert(error.message);
        } finally {
            ui.fileUploadInput.value = '';
        }
    }

    async function handleChatSubmit(e) {
        e.preventDefault();
        const query = ui.messageInput.value.trim();
        if (!query || !state.currentProjectId) return;

        const userMessage = { role: 'user', content: query };
        state.chatHistory.push(userMessage);
        renderChatMessage(userMessage);
        ui.messageInput.value = '';
        ui.sendButton.disabled = true;

        try {
            const assistantMessage = await api.postChat(state.currentProjectId, query, state.chatHistory);
            state.chatHistory.push(assistantMessage);
            // 마지막 메시지만 다시 렌더링 (중복 방지)
            renderChatMessage(assistantMessage);
            await handleLoadDatasets(); 
        } catch (error) {
            console.error(error);
            renderChatMessage({ role: 'assistant', error: error.message });
        } finally {
            ui.sendButton.disabled = false;
        }
    }

    // --- 초기화 ---
    function init() {
        handleLoadProjects();
        ui.projectList.addEventListener('click', handleSelectProject);
        ui.projectList.addEventListener('click', handleDeleteProject);
        ui.createProjectBtn.addEventListener('click', handleCreateProject);
        ui.fileUploadInput.addEventListener('change', handleFileUpload);
        ui.chatForm.addEventListener('submit', handleChatSubmit);
    }

    init();
});