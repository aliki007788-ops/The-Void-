<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>The Void</title>

<script src="https://telegram.org/js/telegram-web-app.js"></script>

<style>
:root {
  --gold: #FFD700;
  --bg: #050505;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: white;
  font-family: "Georgia", serif;
  overflow: hidden;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at center, rgba(255,215,0,0.08), transparent 65%);
  pointer-events: none;
}

#ui-container {
  text-align: center;
  z-index: 10;
  transition: opacity 1s ease;
}

h1 {
  color: var(--gold);
  letter-spacing: 8px;
  font-weight: 400;
  font-size: 42px;
  margin-bottom: 30px;
  text-shadow: 0 0 20px rgba(255,215,0,.3);
}

.subtitle {
  color: #aaa;
  font-weight: 300;
  margin-bottom: 40px;
}

input {
  background: transparent;
  border: none;
  border-bottom: 1px solid #444;
  color: var(--gold);
  font-size: 22px;
  text-align: center;
  padding: 12px;
  width: 80%;
  outline: none;
}

input::placeholder { color: #444; }

.release-btn {
  margin-top: 60px;
  background: transparent;
  color: var(--gold);
  border: 1px solid var(--gold);
  padding: 16px 60px;
  letter-spacing: 4px;
  cursor: pointer;
  transition: all .4s ease;
}

.release-btn:hover {
  background: var(--gold);
  color: var(--bg);
  box-shadow: 0 0 40px rgba(255,215,0,.5);
}

canvas {
  position: absolute;
  inset: 0;
  z-index: 5;
  pointer-events: none;
  filter: blur(.3px);
}

#final-message {
  position: absolute;
  color: var(--gold);
  font-size: 22px;
  letter-spacing: 6px;
  opacity: 0;
  transition: opacity 2s ease;
  z-index: 20;
}
</style>
</head>

<body>

<canvas id="particle-canvas"></canvas>

<div id="ui-container">
  <h1>THE VOID</h1>
  <p class="subtitle">What burden do you wish to erase forever?</p>
  <input id="burden-input" placeholder="Anxiety, Debt, Her…" autocomplete="off">
  <br>
  <button class="release-btn" onclick="startReleaseSequence()">RELEASE</button>
</div>

<div id="final-message">VOID ACCEPTED</div>

<script>
const tg = window.Telegram.WebApp;
tg.expand();
tg.setBackgroundColor("#050505");
tg.setHeaderColor("#050505");

const canvas = document.getElementById("particle-canvas");
const ctx = canvas.getContext("2d");
resize();

window.addEventListener("resize", resize);
function resize() {
  canvas.width = innerWidth;
  canvas.height = innerHeight;
}

let particles = [];

class Particle {
  constructor(x, y) {
    const a = Math.random() * Math.PI * 2;
    const p = Math.random() * 7 + 2;

    this.x = x;
    this.y = y;
    this.vx = Math.cos(a) * p;
    this.vy = Math.sin(a) * p;

    this.life = 1;
    this.size = Math.random() * 2 + 1;

    this.gold = `rgb(255, ${200 + Math.random()*55}, ${60 + Math.random()*60})`;
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    this.vx *= 0.96;
    this.vy *= 0.96;
    this.vy += 0.03;
    this.life -= 0.015;
  }

  draw() {
    ctx.globalAlpha = this.life;
    ctx.shadowBlur = 18;
    ctx.shadowColor = this.gold;
    ctx.fillStyle = this.gold;
    ctx.fillRect(this.x, this.y, this.size, this.size);
    ctx.globalAlpha = 1;
  }
}

function initTextExplosion(text) {
  particles = [];

  const tmp = document.createElement("canvas");
  const t = tmp.getContext("2d");

  tmp.width = canvas.width;
  tmp.height = canvas.height;

  t.fillStyle = "#FFD700";
  t.textAlign = "center";
  t.textBaseline = "middle";
  t.font = "bold 80px Georgia";
  t.fillText(text, tmp.width/2, tmp.height/2);

  const data = t.getImageData(0,0,tmp.width,tmp.height).data;

  for (let y=0; y<tmp.height; y+=3) {
    for (let x=0; x<tmp.width; x+=3) {
      if (data[(y*tmp.width+x)*4+3] > 150) {
        particles.push(new Particle(x,y));
      }
    }
  }
}

function animateExplosion() {
  ctx.clearRect(0,0,canvas.width,canvas.height);

  particles.forEach(p => {
    p.update();
    p.draw();
  });

  particles = particles.filter(p => p.life > 0);

  if (particles.length) {
    requestAnimationFrame(animateExplosion);
  } else {
    showFinal();
  }
}

function startReleaseSequence() {
  const input = document.getElementById("burden-input");
  const text = input.value.trim();

  if (!text) {
    tg.HapticFeedback.notificationOccurred("error");
    return;
  }

  tg.HapticFeedback.impactOccurred("heavy");
  document.getElementById("ui-container").style.opacity = 0;

  initTextExplosion(text);
  animateExplosion();
}

function showFinal() {
  document.getElementById("final-message").style.opacity = 1;
  tg.HapticFeedback.notificationOccurred("success");

  setTimeout(() => {
    tg.sendData(JSON.stringify({
      action: "create_invoice",
      need: document.getElementById("burden-input").value
    }));
  }, 2000);
}
</script>

</body>
</html>
