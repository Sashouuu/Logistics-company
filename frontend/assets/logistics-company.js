document.addEventListener('DOMContentLoaded',()=>{
  const navToggle=document.getElementById('navToggle');
  const mainNav=document.getElementById('mainNav');
  if(navToggle){navToggle.addEventListener('click',()=>{
    if(mainNav.style.display==='block'){mainNav.style.display=''}else{mainNav.style.display='block'}
  })}

  const form=document.getElementById('contactForm');
  const msg=document.getElementById('formMsg');
  if(form){
    form.addEventListener('submit',async e=>{
      e.preventDefault();
      const data=new FormData(form);
      const payload={
        name:data.get('name'),
        email:data.get('email'),
        message:data.get('message')
      };
      try{
        const response=await fetch('/api/contact',{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify(payload)
        });
        const result=await response.json();
        if(response.ok){
          msg.textContent=result.message||'Съобщението беше изпратено!';
          msg.style.color='green';
          form.reset();
        }else{
          msg.textContent=result.error||'Грешка при изпращане.';
          msg.style.color='red';
        }
      }catch(error){
        msg.textContent='Грешка при свързване със сървъра.';
        msg.style.color='red';
        console.error('Contact form error:',error);
      }
    })
  }
});
