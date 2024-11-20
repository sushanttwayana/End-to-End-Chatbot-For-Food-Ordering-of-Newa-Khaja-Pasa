document.addEventListener("DOMContentLoaded", function () {
    const sliderContainer = document.querySelector(".slider-container");
    const images = document.querySelectorAll(".slider-image");
    const imageCount = images.length;
    let currentIndex = 0;

    function autoSlide() {
        currentIndex = (currentIndex + 1) % imageCount; // Loop back to the first image
        const offset = -currentIndex * 600; // Assuming each image is 600px wide
        sliderContainer.style.transform = `translateX(${offset}px)`;
    }

    // Start the automatic slider
    setInterval(autoSlide, 3000); // Slide every 3 seconds
});
