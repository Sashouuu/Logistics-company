document.addEventListener('DOMContentLoaded',()=>{
  const navToggle=document.getElementById('navToggle');
  const mainNav=document.getElementById('mainNav');
  if(navToggle){navToggle.addEventListener('click',()=>{
    if(mainNav.style.display==='block'){mainNav.style.display=''}else{mainNav.style.display='block'}
  })}

  const form=document.getElementById('contactForm');
  const msg=document.getElementById('formMsg');
  if(form){
    form.addEventListener('submit',e=>{
      e.preventDefault();
      const data=new FormData(form);
      // For demo: just show a success message
      msg.textContent = 'Благодарим ви! Съобщението беше изпратено (демо).';
      form.reset();
    })
  }
});
