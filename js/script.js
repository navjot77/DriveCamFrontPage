/**
 * Created by navjotsingh on 2/14/17.
 */

$(document).ready(function(){

/*

    $(window).scroll(function() {
    var scroll_pos = window.pageYOffset;
    if(scroll_pos>=15) {
       $("nav").css("background-color","black");
    }
    else
    {
    	 $("nav").css("background-color","white");
    }
    });
*/

    //$('.caption').effect("bounce", {
      //  times: 4,
        //distance: 250
    //}, 1500);


    jQuery('.text').addClass("hidde").viewportChecker({
	    classToAdd: 'visibl animated bounceInUp', // Class to add to the elements when they are visible
	    offset: 70
	   });




  $('#email').blur(function () {
  	var x= document.getElementById("email").value;
	if ((x.search(/@/)) == -1)
	{
		document.getElementById("form-error").style.display="block";

		/*var para = document.createElement("p");
		var node = document.createTextNode("Enter correct email-ID");
		para.appendChild(node);

		var element = document.getElementById("email");
		element.appendChild(para);
		element.style.color="red";*/
	}
	else{

		document.getElementById("email-error").style.display="None";
	}


  });

  $('#cell').blur(function () {
  	var x= document.getElementById("cell").value;
	//if ((x.search([a-z]/i)) == -1)
	var pat=/\D/g;
	if (((x.search(pat)) == -1) && (x.length == 10))
	{
		document.getElementById("form-error-tel").style.display="None";

	}
	else{

		document.getElementById("form-error-tel").style.display="block";

	}


  });

});
