<script lang="ts">
  let { size = "50px", message = "Загрузка данных..." } = $props();
</script>

<div class="spinner-container">
  <div class="gd-cube-loader" style="--size: {size}">
    <div class="cube-part"></div>
  </div>
  {#if message}
    <p class="loading-text">{message}</p>
  {/if}
</div>

<style>
  .spinner-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    width: 100%;
  }

  .gd-cube-loader {
    width: var(--size);
    height: var(--size);
    background-color: var(--primary);
    border: 3px solid #fff;
    border-radius: 8px;
    box-shadow: 0 0 20px rgba(249, 115, 22, 0.5);
    animation: cube-spin 1.5s infinite ease-in-out;
  }

  .loading-text {
    margin-top: 20px;
    color: #fff;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-size: 0.8rem;
    opacity: 0.7;
    animation: pulse 1.5s infinite alternate;
  }

  @keyframes cube-spin {
    0% {
      transform: rotate(0deg) scale(1);
    }
    50% {
      transform: rotate(180deg) scale(1.1);
    }
    100% {
      transform: rotate(360deg) scale(1);
    }
  }

  @keyframes pulse {
    from {
      opacity: 0.4;
    }
    to {
      opacity: 0.8;
    }
  }
</style>
