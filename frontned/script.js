// Emoji floating logic
const emojiTypes = ['😊', '😢', '😠', '😲', '😐', '😁', '😭', '😡', '😳', '🤔', '❤️', '😍', '😨', '😱'];

function createFloatingEmoji() {
  const emoji = document.createElement('div');
  emoji.className = 'emoji';
  emoji.textContent = emojiTypes[Math.floor(Math.random() * emojiTypes.length)];

  const size = Math.random() * 40 + 40;
  const left = Math.random() * 100;
  const delay = Math.random() * 10;

  emoji.style.left = `${left}%`;
  emoji.style.fontSize = `${size}px`;
  emoji.style.setProperty('--delay', delay.toFixed(2));

  document.querySelector('.emoji-bg').appendChild(emoji);
  setTimeout(() => emoji.remove(), 12000);
}

setInterval(createFloatingEmoji, 400);

// Run only after DOM is fully loaded
window.addEventListener('DOMContentLoaded', () => {

  // Attach to window so it's available for inline onclick
  window.detectEmotion = async function () {
    const text = document.getElementById('inputText').value;
    if (!text.trim()) return;

    try {
      const response = await fetch('http://127.0.0.1:8000/predict/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ sentence: text })
      });

      const result = await response.json();

      const labels = Object.keys(result.emotion_percentages);
      const data = Object.values(result.emotion_percentages);

      // Show emotion
      document.getElementById('emotionResult').innerText = result.predicted_emotion;

      // Render chart
      const chartEl = document.getElementById('emotionChart');
      if (!chartEl) return;
      const ctx = chartEl.getContext('2d');
      if (!ctx) return;

      if (window.myChart) window.myChart.destroy();

      window.myChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Emotion Confidence (%)',
            data: data,
            backgroundColor: '#fb7185',
            borderRadius: 10
          }]
        },
        options: {
          animation: {
            duration: 1000,
            easing: 'easeOutBounce'
          },
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { color: '#0f172a' },
              grid: { color: '#ccc' }
            },
            x: {
              ticks: { color: '#0f172a' },
              grid: { display: false }
            }
          }
        }
      });

      // === Show Recommendations ===
      const movie = result.recommendations.movie;
      const series = result.recommendations.series;
      const song = result.recommendations.song;

      // Movie
      document.getElementById('movie-title').innerText = movie["Series_Title"] || '--';
      document.getElementById('movie-year').innerText = movie["Released_Year"] || '--';
      document.getElementById('movie-certificate').innerText = movie["Certificate"] || '--';
      document.getElementById('movie-runtime').innerText = movie["Runtime"] || '--';
      document.getElementById('movie-genre').innerText = movie["Genre"] || '--';
      document.getElementById('movie-rating').innerText = movie["IMDB_Rating"] || '--';
      document.getElementById('movie-description').innerText = movie["Overview"] || '--';

      // TV Show
      document.getElementById('tv-title').innerText = series["Series Title"] || '--';
      document.getElementById('tv-year').innerText = series["Year Released"] || '--';
      document.getElementById('tv-certificate').innerText = series["Content Rating"] || '--';
      document.getElementById('tv-rating').innerText = series["IMDB Rating"] || '--';
      document.getElementById('tv-genre').innerText = series["Genre"] || '--';
      document.getElementById('tv-description').innerText = series["Description"] || '--'; 
      document.getElementById('tv-seasons').innerText = series["No of Seasons"] || '--';   
      document.getElementById('tv-platform').innerText = series["Streaming Platform"] || '--';

      // Song
      document.getElementById('song-name').innerText = song["track_name"] || '--';
      document.getElementById('song-artist').innerText = song["artist"] || '--';
      document.getElementById('song-valence').innerText = song["valence"] || '--';
      document.getElementById('song-energy').innerText = song["energy"] || '--';
      document.getElementById('song-danceability').innerText = song["danceability"] || '--';
      document.getElementById('song-tempo').innerText = song["tempo"] || '--';
      document.getElementById('song-acousticness').innerText = song["acousticness"] || '--';
      document.getElementById('song-speechiness').innerText = song["speechiness"] || '--';

    } catch (error) {
      console.error('Error:', error);
      document.getElementById('emotionResult').innerText = 'Error detecting emotion.';
    }
  };

});
