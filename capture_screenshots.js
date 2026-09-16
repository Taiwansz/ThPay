const fs = require('fs');
const path = require('path');
const puppeteer = require('/tmp/test-puppeteer/node_modules/puppeteer');

const OUTPUT_DIR = '/root/ThPay/docs/screenshots';

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function capture() {
  console.log('Iniciando captura programatica de screenshots em alta resolucao...');
  
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium-headless-shell',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--hide-scrollbars'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({
    width: 1440,
    height: 960,
    deviceScaleFactor: 1.5
  });

  // Navigate to local index.html
  await page.goto('file:///root/ThPay/ui/index.html', { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1200)); // Wait for Tailwind CDN and fonts

  // 1. Dashboard de Folha Continua (Visao DP)
  console.log('Capturando 01_dashboard_folha_continua.png...');
  await page.evaluate(() => switchView('directory'));
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '01_dashboard_folha_continua.png'), fullPage: false });

  // 2. Raio-X do Holerite e Custo Empresa (Drawer)
  console.log('Capturando 02_raio_x_holerite_drawer.png...');
  await page.evaluate(() => openDrawer(0));
  await new Promise(r => setTimeout(r, 500));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '02_raio_x_holerite_drawer.png'), fullPage: false });

  // Fechar drawer
  await page.evaluate(() => closeDrawer());
  await new Promise(r => setTimeout(r, 300));

  // 3. Portal do Colaborador - Beneficios Flexiveis
  console.log('Capturando 03_portal_colaborador_beneficios.png...');
  await page.evaluate(() => {
    switchView('employee-portal');
    switchPortalTab('benefits');
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '03_portal_colaborador_beneficios.png'), fullPage: false });

  // 4. Central de Chamados (Service Desk)
  console.log('Capturando 04_central_chamados_service_desk.png...');
  await page.evaluate(() => {
    switchPortalTab('tickets');
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '04_central_chamados_service_desk.png'), fullPage: false });

  // 5. Detalhes do Chamado e Timeline de Interacoes (Drawer)
  console.log('Capturando 05_chamado_detalhes_timeline.png...');
  await page.evaluate(() => {
    openTicketDetails('TCK-2026-0904');
  });
  await new Promise(r => setTimeout(r, 500));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '05_chamado_detalhes_timeline.png'), fullPage: false });

  // Fechar detalhes do chamado
  await page.evaluate(() => closeTicketDetails());
  await new Promise(r => setTimeout(r, 300));

  // 6. Desempenho & Leaderboard Operacional
  console.log('Capturando 06_leaderboard_desempenho.png...');
  await page.evaluate(() => {
    switchPortalTab('leaderboard');
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '06_leaderboard_desempenho.png'), fullPage: false });

  // 7. Simulador de Cenarios (Wasm Edge)
  console.log('Capturando 07_simulador_cenarios.png...');
  await page.evaluate(() => {
    switchView('simulator');
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '07_simulador_cenarios.png'), fullPage: false });

  // 8. eSocial e Guias Pix FGTS Digital
  console.log('Capturando 08_esocial_guias_pix.png...');
  await page.evaluate(() => {
    switchView('esocial');
  });
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '08_esocial_guias_pix.png'), fullPage: false });

  await browser.close();
  console.log('Todas as 8 capturas foram concluidas com sucesso em:', OUTPUT_DIR);
}

capture().catch(err => {
  console.error('Erro durante a captura:', err);
  process.exit(1);
});
