javascript:(async()=>{try{const html=document.documentElement.outerHTML;await navigator.clipboard.writeText(html);}catch(e){console.error(e);}})();
