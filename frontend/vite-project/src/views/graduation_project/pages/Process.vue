<template>
  <div class="achieve-container">
    <!-- 左侧侧边栏 -->
    <aside class="sidebar">
      <div class="logo-area">
        <div class="logo-content">
          <div class="logo-icon">C</div>
          <span class="logo-text">CBANK</span>
        </div>
        <div class="header-actions">
          <div class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
          </div>
          <div class="profile-pic">
            <img src="https://i.pravatar.cc/150?img=32" alt="Profile" />
          </div>
        </div>
      </div>

      <div class="search-bar">
        <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <span>Search</span>
      </div>

      <div class="balance-section">
        <div class="balance-card pink">
          <span class="label">Total Balance</span>
          <span class="amount">$ 2 200</span>
        </div>
        <div class="balance-card blue">
          <span class="label">My Card</span>
          <span class="amount">$ 12 029</span>
        </div>
      </div>

      <div class="section-title">Services</div>
      <div class="services-grid">
        <div class="service-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg> Insurance</div>
        <div class="service-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg> Payments</div>
        <div class="service-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg> Utility</div>
        <div class="service-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 1 21 5 17 9"></polyline><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg> Transfer</div>
        <div class="service-item"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg> Mobile</div>
        <div class="service-item add"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg> Add</div>
      </div>

      <div class="bottom-icons">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path></svg>
      </div>
    </aside>

    <!-- 右侧主内容 -->
    <main class="main-content">
      <!-- 背景装饰圆 -->
      <div class="bg-circle"></div>

      <!-- 顶部导航 -->
      <nav class="top-nav">
        <a href="#" class="active">Dashboard</a>
        <a href="#">Expenses</a>
        <a href="#">History</a>
        <a href="#">Actions</a>
      </nav>

      <!-- 核心内容区 -->
      <div class="content-body">
        <!-- 左侧：卡片与图表 -->
        <div class="left-col">
          <div class="main-card">
            <div class="card-top">
              <span class="card-type">**** 1902</span>
              <svg width="30" height="30" viewBox="0 0 24 24" fill="white"><circle cx="12" cy="12" r="10" fill="#FF5F57"/><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" fill="#EB6709"/></svg>
            </div>
            <div class="card-amount">$ 2 200</div>
            <div class="card-name">Emma Watson</div>
          </div>

          <div class="chart-box">
            <div class="chart-header">
              <span>Statistics</span>
              <span class="period">Week</span>
            </div>
            <div class="bars">
              <div class="bar" style="height: 40%"></div>
              <div class="bar" style="height: 70%"></div>
              <div class="bar" style="height: 50%"></div>
              <div class="bar" style="height: 90%"></div>
              <div class="bar active" style="height: 60%"></div>
              <div class="bar" style="height: 30%"></div>
              <div class="bar" style="height: 50%"></div>
            </div>
            <div class="days">
              <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
            </div>
          </div>
        </div>

        <!-- 右侧：气泡与列表 -->
        <div class="right-col">
          <div class="bubbles">
            <div class="bubble purple">
              <span class="title">Electronics</span>
              <span class="val">$ 1392</span>
            </div>
            <div class="bubble blue">
              <span class="title">Services</span>
              <span class="val">$ 1201</span>
            </div>
            <div class="bubble orange">
              <span class="title">Travel</span>
              <span class="val">$ 1280</span>
            </div>
            <div class="bubble more">
              <span>More</span>
            </div>
          </div>

          <div class="lists">
            <div class="list-section">
              <h4>This Week</h4>
              <div class="list-item">
                <div class="icon walmart">W</div>
                <div class="details">
                  <span class="name">Walmart</span>
                  <span class="date">12:00</span>
                </div>
                <span class="amount">-$21</span>
              </div>
              <div class="list-item">
                <div class="icon apple"></div>
                <div class="details">
                  <span class="name">Apple Store</span>
                  <span class="date">10:30</span>
                </div>
                <span class="amount">-$35</span>
              </div>
            </div>

            <div class="list-section">
              <h4>Popular Transfers</h4>
              <div class="avatars">
                <div class="avatar"><img src="https://i.pravatar.cc/150?img=1" /><span class="amt">-$251</span></div>
                <div class="avatar"><img src="https://i.pravatar.cc/150?img=2" /><span class="amt">-$234</span></div>
                <div class="avatar"><img src="https://i.pravatar.cc/150?img=3" /><span class="amt">-$151</span></div>
                <div class="avatar"><img src="https://i.pravatar.cc/150?img=4" /><span class="amt">-$105</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
  // 这里可以放置交互逻辑
</script>

<style scoped>
  /* 容器基础设置 */
  .achieve-container {
    width: 980px;
    height: 560px;
    background: #f4f6fc; /* 整体背景色 */
    border-radius: 24px;
    display: flex;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #333;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    position: relative;
  }

  /* --- 左侧侧边栏 --- */
  .sidebar {
    width: 240px;
    background: #fff;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 24px;
    z-index: 2;
  }

  .logo-area {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .logo-content {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    font-size: 18px;
    color: #333;
  }

  .logo-icon {
    width: 32px;
    height: 32px;
    background: #333;
    color: #fff;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
  }

  .header-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .menu-icon {
    cursor: pointer;
    color: #888;
  }

  .profile-pic img {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    object-fit: cover;
  }

  .search-bar {
    background: #f0f2f5;
    padding: 10px 16px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #888;
    font-size: 14px;
  }

  .balance-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .balance-card {
    padding: 16px;
    border-radius: 16px;
    color: white;
    display: flex;
    flex-direction: column;
    gap: 4px;
    cursor: pointer;
    transition: transform 0.2s;
  }

  .balance-card:hover {
    transform: translateY(-2px);
  }

  .pink { background: #ff8fa3; } /* 修正为更好看的粉色 */
  .blue { background: #7c9bff; }

  .balance-card .label { font-size: 12px; opacity: 0.9; }
  .balance-card .amount { font-size: 18px; font-weight: 700; }

  .section-title {
    font-size: 12px;
    font-weight: 600;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 8px;
  }

  .services-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .service-item {
    background: #f9f9f9;
    padding: 12px;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 500;
    color: #555;
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .service-item:hover {
    background: #f0f0f0;
  }

  .service-item svg { color: #ff8fa3; }
  .service-item.add { color: #888; }
  .service-item.add svg { color: #888; }

  .bottom-icons {
    margin-top: auto;
    display: flex;
    gap: 20px;
    color: #888;
  }

  /* --- 右侧主内容 --- */
  .main-content {
    flex: 1;
    position: relative; /* 关键：为了让背景圆绝对定位相对于它 */
    padding: 32px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* 背景装饰圆 - 核心修复 */
  .bg-circle {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%); /* 真正的居中 */
    width: 480px;
    height: 480px;
    background: radial-gradient(circle, rgba(255,143,163,0.25) 0%, rgba(255,255,255,0) 70%);
    border-radius: 50%;
    z-index: 0; /* 在最底层 */
    pointer-events: none; /* 防止遮挡点击 */
  }

  .top-nav {
    display: flex;
    gap: 32px;
    z-index: 1;
    margin-bottom: 24px;
  }

  .top-nav a {
    text-decoration: none;
    color: #888;
    font-weight: 500;
    font-size: 15px;
    position: relative;
  }

  .top-nav a.active {
    color: #333;
    font-weight: 700;
  }

  .top-nav a.active::after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 50%;
    transform: translateX(-50%);
    width: 6px;
    height: 6px;
    background: #ff8fa3;
    border-radius: 50%;
  }

  /* 内容主体布局 */
  .content-body {
    flex: 1;
    display: flex;
    gap: 32px;
    z-index: 1; /* 内容层级高于背景圆 */
  }

  .left-col {
    display: flex;
    flex-direction: column;
    gap: 24px;
    width: 280px; /* 固定宽度以保证对齐 */
  }

  .main-card {
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
    padding: 24px;
    border-radius: 24px;
    color: white;
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 20px rgba(255, 143, 163, 0.3);
  }

  .card-top {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
    font-size: 14px;
    opacity: 0.9;
  }

  .card-amount {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 8px;
  }

  .card-name {
    font-size: 14px;
    opacity: 0.9;
  }

  .chart-box {
    background: white;
    padding: 20px;
    border-radius: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03);
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 20px;
  }

  .period {
    background: #f0f2f5;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 500;
    color: #555;
  }

  .bars {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    height: 60px;
    margin-bottom: 12px;
  }

  .bar {
    width: 8px;
    background: #f0f2f5;
    border-radius: 4px;
    transition: height 0.3s;
  }

  .bar.active {
    background: #ff8fa3;
  }

  .days {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #888;
  }

  /* 右侧列 */
  .right-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 24px;
    align-items: center; /* 让气泡组居中 */
    justify-content: center;
  }

  .bubbles {
    display: flex;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;
  }

  .bubble {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: white;
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    cursor: pointer;
    transition: transform 0.2s;
  }

  .bubble:hover { transform: scale(1.05); }

  .bubble .title { font-size: 11px; opacity: 0.9; margin-bottom: 4px; }
  .bubble .val { font-size: 16px; }

  .purple { background: #a18cff; }
  .blue { background: #6ecffa; }
  .orange { background: #ff9f7f; }

  .bubble.more {
    background: rgba(255,255,255,0.6);
    color: #555;
    backdrop-filter: blur(5px);
    width: 60px;
    height: 60px;
    font-size: 12px;
  }

  /* 列表区域 */
  .lists {
    display: flex;
    gap: 40px;
    background: rgba(255,255,255,0.6); /* 半透明背景 */
    padding: 20px 30px;
    border-radius: 24px;
    backdrop-filter: blur(10px);
    width: 100%;
    max-width: 400px;
  }

  .list-section h4 {
    font-size: 14px;
    color: #555;
    margin-bottom: 16px;
    font-weight: 600;
  }

  .list-item {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }

  .icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 12px;
    font-weight: bold;
  }

  .walmart { background: #0071ce; }
  .apple { background: #000; }

  .details {
    display: flex;
    flex-direction: column;
    font-size: 12px;
  }

  .details .name { font-weight: 600; color: #333; }
  .details .date { color: #888; font-size: 10px; }

  .amount {
    margin-left: auto;
    font-size: 13px;
    font-weight: 600;
    color: #333;
  }

  .avatars {
    display: flex;
    gap: 12px;
  }

  .avatar {
    position: relative;
    width: 44px;
    height: 44px;
  }

  .avatar img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 2px solid white;
  }

  .avatar .amt {
    position: absolute;
    bottom: -8px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 9px;
    background: white;
    padding: 2px 6px;
    border-radius: 10px;
    font-weight: 600;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    white-space: nowrap;
  }
</style>