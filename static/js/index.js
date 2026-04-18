// ── File input: show selected filename ────────────────────────────────────────
const fileInput = document.getElementById('fileInput');

fileInput.addEventListener('change', function () {
  const file = this.files[0];
  if (!file) return;
  document.getElementById('selectedFileName').textContent = file.name;
  document.getElementById('fileTypeIcon').textContent     = file.name.endsWith('.pdf') ? '📕' : '📄';
  document.getElementById('selectedFile').classList.add('show');
  hideError();
});


// ── Drag-and-drop support ──────────────────────────────────────────────────────
const dropZone = document.getElementById('dropZone');

dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');

  const file = e.dataTransfer.files[0];
  if (file && (file.name.endsWith('.csv') || file.name.endsWith('.pdf'))) {
    fileInput.files = e.dataTransfer.files;
    document.getElementById('selectedFileName').textContent = file.name;
    document.getElementById('fileTypeIcon').textContent     = file.name.endsWith('.pdf') ? '📕' : '📄';
    document.getElementById('selectedFile').classList.add('show');
  } else {
    showError('Only .csv and .pdf files are supported.');
  }
});


// ── Error helpers ──────────────────────────────────────────────────────────────
function showError(msg) {
  document.getElementById('errorText').textContent = msg;
  document.getElementById('errorMsg').classList.add('show');
}
function hideError() {
  document.getElementById('errorMsg').classList.remove('show');
}


// ── Upload and analyze file ────────────────────────────────────────────────────
async function analyzeFile() {
  const file = fileInput.files[0];
  if (!file) { showError('Please select a CSV or PDF file first.'); return; }

  hideError();
  const isPDF = file.name.endsWith('.pdf');
  showLoading(
    isPDF ? 'Reading your PDF...' : 'Analyzing your finances...',
    isPDF ? 'Extracting transactions from bank statement 📄' : 'Crunching numbers with AI magic ✨'
  );

  const analyzeBtn = document.getElementById('analyzeBtn');
  analyzeBtn.disabled = true;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res  = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.error) {
      hideLoading();
      showError(data.error);
      analyzeBtn.disabled = false;
      return;
    }
    sessionStorage.setItem('paisaData', JSON.stringify(data));
    window.location.href = '/dashboard';
  } catch (e) {
    hideLoading();
    analyzeBtn.disabled = false;
    showError('Failed to connect to server. Make sure Flask is running.');
  }
}


// ── Demo data ──────────────────────────────────────────────────────────────────
async function useDemo() {
  hideError();
  showLoading('Loading demo data...', 'Using sample Indian transactions ⚡');

  const formData = new FormData();
  formData.append('use_demo', '1');

  try {
    const res  = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.error) { hideLoading(); showError(data.error); return; }
    sessionStorage.setItem('paisaData', JSON.stringify(data));
    window.location.href = '/dashboard';
  } catch (e) {
    hideLoading();
    showError('Failed to connect to server. Make sure Flask is running.');
  }
}


// ── Loading overlay helpers ────────────────────────────────────────────────────
function showLoading(text, sub) {
  document.getElementById('loadingText').textContent = text || 'Analyzing your finances...';
  document.getElementById('loadingSub').textContent  = sub  || 'Crunching numbers with AI magic ✨';
  document.getElementById('loadingOverlay').classList.add('show');
}
function hideLoading() {
  document.getElementById('loadingOverlay').classList.remove('show');
}
