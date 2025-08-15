document.addEventListener("DOMContentLoaded", function () {
    const radioButtons = document.querySelectorAll('input[name="userType"]');
    const businessSection = document.getElementById('infobusiness');
    const jobSection = document.getElementById('infojob');

    // Hide both sections initially
    businessSection.style.display = 'none';
    jobSection.style.display = 'none';

    radioButtons.forEach(radio => {
        radio.addEventListener('change', function () {
            if (this.value === 'job') {
                jobSection.style.display = 'block';
                businessSection.style.display = 'none';
            } else if (this.value === 'business') {
                businessSection.style.display = 'block';
                jobSection.style.display = 'none';
            }
        });
    });
});


// Header scroll behavior
const header = document.getElementById('header');
const formSection = document.querySelector('.form-section');

window.addEventListener('scroll', () => {
    const formTop = formSection.offsetTop;
    const headerHeight = header.offsetHeight;

    if (window.scrollY >= formTop - headerHeight - 10) {
        // Stop the header just above the form
        header.style.position = 'absolute';
        header.style.top = (formTop - headerHeight - 10) + 'px';
    } else {
        // Keep it fixed while scrolling up
        header.style.position = 'fixed';
        header.style.top = '10px';
    }
});

function nextStep(current) {
    const currentInputs = document.querySelectorAll(`#step-${current} input`);
    let allFilled = true;

    currentInputs.forEach(input => {
        if (!input.value.trim()) {
            allFilled = false;
            input.style.borderColor = "red";
        } else {
            input.style.borderColor = "";
        }
    });

    if (!allFilled) return; // Stop if not filled

    // Mark step completed
    document.querySelector(`.step[data-step="${current}"]`).classList.add("completed");

    // Hide current, show next
    document.getElementById(`step-${current}`).classList.add("hidden");
    const next = current + 1;
    if (document.getElementById(`step-${next}`)) {
        document.getElementById(`step-${next}`).classList.remove("hidden");
    }
}

