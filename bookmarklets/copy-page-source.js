javascript:(async()=>{try{const html=await fetch(location.href,{cache:'no-store'}).then(r=>r.text());await navigator.clipboard.writeText(html);}catch(e){console.error(e);}})();
