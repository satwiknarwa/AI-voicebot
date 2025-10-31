let mediaRecorder;
let audioChunks = [];
const recordBtn = document.getElementById('recordBtn');
const status = document.getElementById('status');
const responseText = document.getElementById('responseText');
const responseAudio = document.getElementById('responseAudio');

recordBtn.addEventListener('click', async () => {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    recordBtn.innerText = 'Start Recording';
    return;
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];
  mediaRecorder.start();
  recordBtn.innerText = 'Stop Recording';
  status.innerText = 'Recording...';

  mediaRecorder.ondataavailable = (e) => {
    audioChunks.push(e.data);
  };

  mediaRecorder.onstop = async () => {
    status.innerText = 'Processing...';
    const blob = new Blob(audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');

    const resp = await fetch('/process_audio/', { method: 'POST', body: formData });
    if (!resp.ok) {
      status.innerText = 'Server error';
      return;
    }
    const data = await resp.json();
    responseText.innerText = data.text || '';
    if (data.audio_url) {
      responseAudio.src = data.audio_url;
      responseAudio.play();
    }
    status.innerText = '';
  };
});
