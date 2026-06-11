document.addEventListener("DOMContentLoaded", function() {
    const slides = document.querySelectorAll('.slide');
    const headings = [
      "Empowering<br>Your Health<br>Journey",
      "Advanced<br>Medical Care<br>For You"
    ];
    let index = 0;

    function updateHeading() {
      document.getElementById("heroTitle").innerHTML = headings[index];
    }

    function showSlide(){
        document.getElementById("slides")
                .style.transform = `translateX(-${index * 100}%)`;
        updateHeading();
    }

    window.nextSlide = function(){
        index++;
        if (index >= slides.length) index = 0;
        showSlide();
    };
    window.prevSlide = function(){
        index--;
        if (index < 0) index = slides.length - 1;
        showSlide();
    };

    showSlide();

    const slider = document.getElementById("slider");
    function slideRight(){
        slider.scrollLeft += 330;
    }
    function slideLeft(){
        slider.scrollLeft -= 330;
    }
    window.slideRight = slideRight;
    window.slideLeft = slideLeft;
});