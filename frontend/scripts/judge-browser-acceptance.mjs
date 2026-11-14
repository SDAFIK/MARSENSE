import {chromium} from "playwright";
import assert from "node:assert/strict";
import {mkdir} from "node:fs/promises";
const origin=process.env.JUDGE_BASE_URL||"http://127.0.0.1:3005";
const output="test-results/judge-resilience";
await mkdir(output,{recursive:true});
const browser=await chromium.launch({args:["--enable-unsafe-swiftshader"]});
const errors=[];
async function scenario(width,height,label) {
  const context=await browser.newContext({viewport:{width,height},reducedMotion:"reduce"});
  const page=await context.newPage();
  page.setDefaultTimeout(15000);
  page.on("pageerror",e=>errors.push(e.message));
  // All /api/** endpoints, even health, are unavailable. Static judge assets
  // use /judge-assets, and all mission mutations stay in browser session storage.
  let blocked=0;
  await page.route("**/api/**",route=>{blocked++;return route.abort();});
  const button=name=>page.getByRole("button",{name,exact:true});
  const visible=locator=>locator.waitFor({state:"visible"});
  const text=value=>visible(page.getByText(value,{exact:true}));
  async function capture(name) {
    await page.waitForFunction(()=>Array.from(document.images).filter(img=>img.getClientRects().length>0).every(img=>img.complete&&img.naturalWidth>0));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),label+" horizontal overflow "+name);
    await page.screenshot({path:output+"/"+label+"-"+name+".png",fullPage:true,animations:"disabled"});
  }
  try {
    await page.goto(origin+"/guide");
    await button("Launch Live Demo").click();
    await page.waitForURL(origin+"/demo");
    await visible(page.getByRole("heading",{name:"Jezero reconnaissance."}));
    const blockedAtEntry=blocked;
    await capture("expect");
    await button("Go to observation").click();
    await button("Analyze terrain").click();
    await text("Obstacle-rich terrain");
    await button("Open human review").click();
    await button("Request more evidence").click();
    await text("More evidence requested. Route Alpha remains unchanged.");
    await button("Review another replay").click();
    await button("Open human review").click();
    await button("Reject observation").click();
    await text("Rejected. Route Alpha remains active. No knowledge is added.");
    await button("Restart demo").click();
    await button("Go to observation").click();
    await capture("observe");
    await button("Analyze terrain").click();
    await capture("compare");
    await button("Open human review").click();
    await button("Confirm observation").click();
    await visible(page.getByRole("heading",{name:"The living map adapts."}));
    await text("Route Beta");
    await button("Calculate route options").click();
    await visible(page.getByRole("button",{name:/Lowest modeled cost/}));
    await visible(page.getByRole("button",{name:/Alternative 1/}));
    await page.getByRole("button",{name:/Alternative 1/}).click();
    await button("Before").click();
    await button("After").click();
    await capture("learn");
    await page.reload();
    await visible(page.getByRole("heading",{name:"The living map adapts."}));
    await button("Continue to next EVA").click();
    await visible(page.getByRole("heading",{name:"One verified record inherited."}));
    await capture("inherit");
    await page.reload();
    await visible(page.getByRole("heading",{name:"One verified record inherited."}));
    assert.equal(blocked,blockedAtEntry,"Browser judge mode must not call any API endpoint");
    await button("Reset demo").click();
    await visible(page.getByRole("heading",{name:"Start with the orbital prior"}));
    await page.reload();
    await visible(page.getByRole("heading",{name:"Start with the orbital prior"}));
    // A separate context is always a fresh guest and cannot see this tab's data.
    const other=await browser.newContext();const second=await other.newPage();
    await second.goto(origin+"/demo");
    await second.getByRole("heading",{name:"Start with the orbital prior"}).waitFor();
    await other.close();
    console.log(label+": full six-stage mission passed with all API calls blocked; alternatives, reject, more evidence, reload, reset and isolation passed");
  }finally{await context.close();}
}
try{await scenario(1440,1000,"desktop");await scenario(390,844,"mobile");assert.deepEqual(errors,[]);console.log("MARSENSE browser-only judge mode: all outage acceptance tests passed.");}finally{await browser.close();}
