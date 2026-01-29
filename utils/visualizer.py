# utils/visualizer.py
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from typing import Optional

class GridVisualizer:
    """Visualizes motor grid states"""
    
    @staticmethod
    def plot_grid(grid_array: np.ndarray, title: str = "Motor Grid", 
                  cmap: str = 'viridis', save_path: Optional[str] = None):
        """Create a 2D plot of the grid"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.imshow(grid_array, cmap=cmap, aspect='auto')
        plt.colorbar(im, ax=ax, label='Intensity')
        
        # Add grid lines
        ax.set_xticks(np.arange(-0.5, grid_array.shape[1], 1), minor=True)
        ax.set_yticks(np.arange(-0.5, grid_array.shape[0], 1), minor=True)
        ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5)
        
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_title(title)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"[Viz] Plot saved: {save_path}")
        
        plt.show()
        return fig
    
    @staticmethod
    def plot_3d_grid(grid_array: np.ndarray, title: str = "3D Motor Grid"):
        """Create a 3D visualization of the grid"""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        x = np.arange(grid_array.shape[1])
        y = np.arange(grid_array.shape[0])
        X, Y = np.meshgrid(x, y)
        
        # Create surface plot
        surf = ax.plot_surface(X, Y, grid_array, cmap='plasma',
                              linewidth=0, antialiased=True)
        
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Intensity')
        
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_zlabel('Intensity')
        ax.set_title(title)
        
        plt.show()
        return fig
    
    @staticmethod
    def create_animation(grid_manager, pattern_func, duration: float = 5.0, 
                        fps: int = 10, output_path: str = "animation.mp4"):
        """Create an animation of pattern execution (requires matplotlib.animation)"""
        try:
            import matplotlib.animation as animation
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            def update(frame):
                ax.clear()
                t = frame / fps
                
                # Update grid
                for (x, y), motor in grid_manager.grid.items():
                    intensity = pattern_func(x, y, t)
                    grid_manager.set_intensity(x, y, intensity)
                
                # Get current grid state
                grid_array = grid_manager.get_grid_array('intensity')
                
                im = ax.imshow(grid_array, cmap='plasma', vmin=0, vmax=1)
                ax.set_title(f"Time: {t:.2f}s")
                return [im]
            
            ani = animation.FuncAnimation(fig, update, 
                                         frames=int(duration * fps),
                                         interval=1000/fps, blit=True)
            
            # Save animation
            ani.save(output_path, writer='ffmpeg', fps=fps)
            print(f"[Viz] Animation saved: {output_path}")
            
            plt.close(fig)
            return ani
            
        except ImportError:
            print("[Viz] Matplotlib animation not available")
            return None