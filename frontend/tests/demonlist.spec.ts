import { test, expect } from '@playwright/test';

test('homepage loads and shows levels', async ({ page }) => {
  await page.goto('/');
  // Ждем, пока исчезнет наш новый лоадер
  await expect(page.locator('text=Синхронизация...')).not.toBeVisible();
  
  // Проверяем заголовок
  await expect(page).toHaveTitle(/ДВ СЛЕЕРСТВО/);
  
  // Проверяем наличие карточек уровней
  const levelCards = page.locator('.level-card');
  await expect(levelCards.first()).toBeVisible();
});

test('navigation to leaderboard works', async ({ page }) => {
  await page.goto('/');
  // Находим кнопку Топ в навигации
  await page.click('text=Топ');
  await page.click('text=ПК', { force: true });
  
  await expect(page).toHaveURL(/\/leaderboard\/pc/);
  await expect(page.locator('h1')).toContainText('Топ Игроков');
});

test('search levels on homepage', async ({ page }) => {
  await page.goto('/list/pc');
  const searchInput = page.locator('input[placeholder="Поиск уровня..."]');
  await searchInput.fill('Acheron');
  await page.keyboard.press('Enter');
  
  // URL должен измениться
  await expect(page).toHaveURL(/q=Acheron/);
});

test('region profile page loads', async ({ page }) => {
  // Тестируем переход в профиль Хабаровского края
  await page.goto('/leaderboard/regions/pc');
  await page.click('text=Хабаровский Край');
  
  await expect(page.locator('h1')).toContainText('Хабаровский Край');
  await expect(page.locator('text=Профиль региона')).toBeVisible();
});
