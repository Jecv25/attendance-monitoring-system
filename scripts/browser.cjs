// Real Flutter browser verification. Never record login bodies, cookies, or .env values.
const fs = require('node:fs');
const path = require('node:path');
let chromium;
try { ({chromium} = require('playwright')); }
catch { ({chromium} = require('../.tools/browser/node_modules/playwright')); }
const root = path.resolve(__dirname, '..');
const base = process.env.ATTENDANCE_TEST_URL || 'http://127.0.0.1:8000';
const env = Object.fromEntries(fs.readFileSync(path.join(root, '.env'), 'utf8').split(/\r?\n/).filter(x => x.includes('=') && !x.startsWith('#')).map(x => [x.slice(0,x.indexOf('=')),x.slice(x.indexOf('=')+1)]));
const folder = path.join(root, 'evidence/week18/browser');
fs.mkdirSync(folder, {recursive:true});
const results = [];
async function main() {
  const candidates = [process.env.ATTENDANCE_BROWSER, 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].filter(Boolean);
  const executablePath = candidates.find(x=>fs.existsSync(x));
  const browser = await chromium.launch({headless:true, ...(executablePath ? {executablePath} : {})});
  const context = await browser.newContext({viewport:{width:1440,height:1000}});
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  const errors=[];
  const label = value => page.getByLabel(value,{exact:false}).or(page.getByText(value,{exact:false})).first();
  page.on('pageerror', error=>errors.push(error.message));
  const shot = async name => { await page.screenshot({path:path.join(folder,name+'.png'),fullPage:true}); };
  async function navigate(name) {
    const menu = page.getByRole('button',{name:'Open navigation',exact:true});
    if (await menu.isVisible()) await menu.click();
    await page.getByRole('button',{name,exact:true}).click();
  }
  try {
    await page.goto(base,{waitUntil:'networkidle'});
    await page.waitForSelector('flutter-view');
    if(await page.locator('flt-semantics-placeholder').count()) await page.locator('flt-semantics-placeholder').evaluate(el=>el.click());
    await page.getByRole('textbox',{name:'Username'}).waitFor();
    await shot('01-login-desktop');
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.getByText('Enter your password',{exact:true}).waitFor();
    results.push({scenario:'client required-field validation',result:'Passed'});
    await page.getByRole('textbox',{name:'Username'}).click();
    await page.getByRole('textbox',{name:'Username'}).pressSequentially('teacher',{delay:20});
    await page.getByRole('textbox',{name:'Password',exact:true}).click();
    await page.getByRole('textbox',{name:'Password',exact:true}).pressSequentially(env.DEMO_TEACHER_PASSWORD,{delay:20});
    await page.waitForTimeout(250);
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await label('Your attendance overview').waitFor();
    await label('Attendance at a glance').waitFor();
    await shot('02-dashboard-desktop');
    await navigate('Sessions');
    await label('Demonstration attendance').click();
    await page.getByText('Mark all present',{exact:true}).click();
    await page.waitForTimeout(250);
    await page.mouse.move(1100,750);
    await page.mouse.wheel(0,1800);
    await page.waitForTimeout(500);
    const [saved] = await Promise.all([page.waitForResponse(r=>r.url().endsWith('/attendance') && r.request().method()==='PUT'),page.getByRole('button',{name:'Save attendance',exact:true}).click()]);
    if (saved.status()!==200) throw Error('Attendance save did not succeed');
    await label('Saved to the attendance record.').waitFor();
    await shot('03-attendance-saved');
    await page.getByRole('button',{name:'Finalize session',exact:true}).click();
    const [finalized] = await Promise.all([page.waitForResponse(r=>r.url().endsWith('/finalize') && r.request().method()==='POST'),page.getByRole('button',{name:'Confirm',exact:true}).click()]);
    if (finalized.status()!==200) throw Error('Attendance finalization did not succeed');
    await label('Finalized record. Corrections retain their reason and audit history.').waitFor();
    await shot('04-attendance-finalized');
    results.push({scenario:'teacher login → roster → save → finalize',result:'Passed',save_status:200,finalize_status:200});
    await navigate('Reports');
    await label('Attendance summary').waitFor();
    await shot('05-reports-desktop');
    await navigate('Audit history');
    await label('Session finalized').waitFor();
    await shot('06-audit-desktop');
    results.push({scenario:'persisted report and audit history',result:'Passed'});
    await page.route('**/api/dashboard',route=>route.abort('failed'));
    await navigate('Overview');
    await label('Cannot reach the service. Check your connection and retry.').waitFor();
    await shot('07-unavailable-service');
    await page.unroute('**/api/dashboard');
    await page.getByRole('button',{name:'Retry',exact:true}).click();
    await label('Attendance at a glance').waitFor();
    results.push({scenario:'unavailable service and retry recovery',result:'Passed'});
    for (const width of [768,390]) {
      await page.setViewportSize({width,height:1000});
      await page.waitForTimeout(500);
      await shot('08-dashboard-'+width);
      await navigate('Sessions');
      await label('Demonstration attendance').waitFor();
      await shot('09-sessions-'+width);
      await navigate('Overview');
      results.push({scenario:'responsive browser width '+width,result:'Passed',scope:'visual capture; Flutter widget tests assert no layout exceptions'});
    }
    await page.keyboard.press('Tab');
    results.push({scenario:'keyboard focus',result:await page.evaluate(()=>document.activeElement!==document.body)?'Passed':'Review required'});
    const anonymous=await browser.newContext();
    const unauthorized=await anonymous.request.get(base+'/api/students');
    if(unauthorized.status()!==401) throw Error('Anonymous access was not rejected');
    results.push({scenario:'anonymous API access',expected_status:401,actual_status:unauthorized.status(),result:'Passed'});
    await anonymous.close();
    if(errors.length) throw Error('Browser reported application errors');
    fs.writeFileSync(path.join(folder,'results.json'),JSON.stringify({executed_at_utc:new Date().toISOString(),browser:await browser.version(),command:'node scripts/browser.cjs',dataset:'Fictional seeded class and 12 learners',results,page_errors:errors},null,2));
    console.log(JSON.stringify({browser_checks:results.length,result:'Passed'}));
  } catch(error) {
    await shot('failure');
    const semantics=await page.locator('flt-semantics').evaluateAll(elements=>elements.map(el=>({role:el.getAttribute('role'),label:el.getAttribute('aria-label')})).filter(el=>el.role||el.label));
    fs.writeFileSync(path.join(folder,'failure-semantics.json'),JSON.stringify(semantics,null,2));
    const safeError=Object.entries(env).filter(([k])=>k.endsWith('_PASSWORD')||k.endsWith('_KEY')).reduce((message,[,v])=>v?message.split(v).join('[REDACTED]'):message,error.message);
    fs.writeFileSync(path.join(folder,'failure.json'),JSON.stringify({executed_at_utc:new Date().toISOString(),results,error:safeError,page_errors:errors},null,2));
    throw error;
  } finally {await browser.close();}
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
