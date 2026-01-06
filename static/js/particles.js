// Particle System for AbdullahHub
class ParticleSystem {
    constructor() {
        this.particles = [];
        this.container = document.querySelector('.particles-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'particles-container';
            document.body.appendChild(this.container);
        }
        this.init();
    }

    init() {
        // Create particles
        this.createParticles(50);
        
        // Animate
        this.animate();
        
        // Handle window resize
        window.addEventListener('resize', () => this.handleResize());
    }

    createParticles(count) {
        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // Random properties
            const size = Math.random() * 5 + 2;
            const x = Math.random() * 100;
            const y = Math.random() * 100;
            const duration = Math.random() * 20 + 10;
            const delay = Math.random() * 5;
            
            // Apply styles
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${x}vw`;
            particle.style.top = `${y}vh`;
            particle.style.opacity = Math.random() * 0.5 + 0.2;
            particle.style.animation = `particle-float ${duration}s linear infinite`;
            particle.style.animationDelay = `${delay}s`;
            
            // Random gradient
            const colors = [
                ['#00f3ff', '#ff00ff'],
                ['#4facfe', '#00f2fe'],
                ['#43e97b', '#38f9d7'],
                ['#f093fb', '#f5576c']
            ];
            const [color1, color2] = colors[Math.floor(Math.random() * colors.length)];
            particle.style.background = `linear-gradient(45deg, ${color1}, ${color2})`;
            
            this.container.appendChild(particle);
            this.particles.push(particle);
        }
    }

    animate() {
        // Update particles
        this.particles.forEach(particle => {
            // Add subtle floating effect
            const currentTop = parseFloat(particle.style.top);
            const newTop = currentTop - 0.1;
            
            if (newTop < -10) {
                particle.style.top = '110vh';
                particle.style.left = `${Math.random() * 100}vw`;
            } else {
                particle.style.top = `${newTop}vh`;
            }
        });
        
        requestAnimationFrame(() => this.animate());
    }

    handleResize() {
        // Update particles on resize if needed
    }
}

// Initialize particle system
document.addEventListener('DOMContentLoaded', () => {
    new ParticleSystem();
});
