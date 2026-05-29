const alarmSound = new Audio('https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg');

function toggleTheme() {
  const body = document.body;
  body.classList.toggle('dark');
  const isDark = body.classList.contains('dark');
  localStorage.setItem('healthpulse-theme', isDark ? 'dark' : 'light');
}

function applySavedTheme() {
  const saved = localStorage.getItem('healthpulse-theme');
  if (saved === 'dark') {
    document.body.classList.add('dark');
  }
}

function requestNotificationPermission() {
  if (!('Notification' in window)) {
    return;
  }
  if (Notification.permission === 'default') {
    Notification.requestPermission();
  }
}

function showNotification(title, body) {
  if (Notification.permission !== 'granted') {
    return;
  }
  const notification = new Notification(title, {
    body,
    icon: '/static/images/app-icon.svg',
  });
  notification.onclick = () => window.focus();
}

function announceMessage(message) {
  if (!('speechSynthesis' in window)) {
    return;
  }
  const utterance = new SpeechSynthesisUtterance(message);
  utterance.rate = 1;
  utterance.pitch = 1;
  speechSynthesis.speak(utterance);
}

function playAlarm() {
  alarmSound.play().catch(() => {
    console.warn('Alarm playback blocked until user interacts with the page.');
  });
}

function triggerSOS() {
  showNotification('Emergency SOS', 'Please seek help or contact emergency services immediately.');
  announceMessage('Emergency SOS activated. Please get help right away.');
  alert('SOS activated! Stay calm and get help if needed.');
}

function notifyWater() {
  showNotification('Hydration Reminder', 'Drink a glass of water to stay refreshed and alert.');
  announceMessage('Time to drink a glass of water. Keep your body hydrated.');
}

function filterMedicines() {
  const query = document.getElementById('searchInput')?.value.toLowerCase() || '';
  const rows = document.querySelectorAll('#medicineTable tbody tr');
  rows.forEach((row) => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
}

function scanQRCode() {
  const sampleInfo = 'Use your QR scanner app to read medicine details.';
  alert(sampleInfo);
}

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker
      .register('/static/service-worker.js')
      .then(() => console.log('Service worker registered'))
      .catch((err) => console.error('Service worker failed', err));
  }
}

function scheduleMedicineReminders() {
  const rows = document.querySelectorAll('#medicineTable tbody tr');
  const now = new Date();
  rows.forEach((row) => {
    const date = row.children[2]?.textContent?.trim();
    const time = row.children[3]?.textContent?.trim();
    if (!date || !time) return;

    const reminderDate = new Date(`${date}T${time}:00`);
    const delay = reminderDate - now;
    if (delay > 0 && delay < 1000 * 60 * 60 * 24) {
      setTimeout(() => {
        const name = row.children[0]?.textContent?.trim();
        showNotification('Medicine Reminder', `${name} is due now.`);
        announceMessage(`Reminder: time for ${name}.`);
        playAlarm();
      }, delay);
    }
  });
}

function initChart() {
  if (typeof progressLabels === 'undefined' || typeof progressCounts === 'undefined') {
    return;
  }
  const ctx = document.getElementById('progressChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: progressLabels,
      datasets: [
        {
          label: 'Taken doses',
          data: progressCounts,
          borderColor: '#5fd7a8',
          backgroundColor: 'rgba(95, 215, 168, 0.18)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: '#68d6ff',
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#c8dcff' } },
        y: {
          grid: { color: 'rgba(255,255,255,0.08)' },
          ticks: { color: '#c8dcff', stepSize: 1 },
        },
      },
    },
  });
}

window.addEventListener('DOMContentLoaded', () => {
  applySavedTheme();
  requestNotificationPermission();
  registerServiceWorker();
  initChart();
  scheduleMedicineReminders();
});
