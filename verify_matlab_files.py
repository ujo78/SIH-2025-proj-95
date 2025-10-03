"""
Verify that exported MATLAB files can be loaded correctly
"""

import scipy.io as sio
import os

def verify_matlab_files():
    """Verify that exported .mat files are valid and loadable"""
    print("Verifying MATLAB files...")
    
    # Find the latest exported files
    export_dir = "matlab_demo_exports"
    if not os.path.exists(export_dir):
        print("❌ Export directory not found. Run matlab_demo.py first.")
        return False
    
    # Get the latest files
    files = os.listdir(export_dir)
    mat_files = [f for f in files if f.endswith('.mat')]
    
    if not mat_files:
        print("❌ No .mat files found. Run matlab_demo.py first.")
        return False
    
    # Sort by timestamp (latest first)
    mat_files.sort(reverse=True)
    
    # Get the latest set of files
    latest_timestamp = mat_files[0].split('_')[-1].replace('.mat', '')
    latest_files = [f for f in mat_files if latest_timestamp in f]
    
    print(f"Checking files with timestamp: {latest_timestamp}")
    
    success_count = 0
    total_files = len(latest_files)
    
    for filename in latest_files:
        filepath = os.path.join(export_dir, filename)
        
        try:
            # Load the .mat file
            data = sio.loadmat(filepath)
            
            # Remove MATLAB metadata keys
            data_keys = [k for k in data.keys() if not k.startswith('__')]
            
            print(f"✅ {filename}")
            print(f"   Data fields: {data_keys}")
            
            # Check specific content based on file type
            if 'trajectories' in filename:
                if 'vehicle_ids' in data:
                    print(f"   Vehicles: {len(data['vehicle_ids'])}")
                if 'positions' in data:
                    print(f"   Position data: {len(data['positions'])} vehicles")
            
            elif 'road_network' in filename:
                if 'nodes' in data:
                    nodes = data['nodes']
                    if hasattr(nodes, 'dtype') and nodes.dtype.names:
                        print(f"   Network structure: nodes with fields {nodes.dtype.names}")
                if 'edges' in data:
                    edges = data['edges']
                    if hasattr(edges, 'dtype') and edges.dtype.names:
                        print(f"   Edge structure: edges with fields {edges.dtype.names}")
            
            elif 'metrics' in filename:
                if 'congestion_metrics' in data:
                    print(f"   Contains congestion metrics")
                if 'flow_metrics' in data:
                    print(f"   Contains flow metrics")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ {filename}: {e}")
    
    print(f"\nVerification complete: {success_count}/{total_files} files valid")
    
    if success_count == total_files:
        print("🎉 All MATLAB files are valid and loadable!")
        return True
    else:
        print("⚠️  Some files have issues")
        return False

def show_matlab_usage():
    """Show how to use the files in MATLAB"""
    print("\n" + "="*60)
    print("MATLAB USAGE INSTRUCTIONS")
    print("="*60)
    
    print("""
To use these files in MATLAB:

1. Open MATLAB and navigate to this directory

2. Load the data files:
   >> data_traj = load('matlab_demo_exports/indian_traffic_demo_trajectories_*.mat');
   >> data_network = load('matlab_demo_exports/indian_traffic_demo_road_network_*.mat');
   >> data_metrics = load('matlab_demo_exports/indian_traffic_demo_metrics_*.mat');

3. Quick visualization:
   >> figure;
   >> hold on;
   >> for i = 1:length(data_traj.vehicle_ids)
   >>     pos = data_traj.positions{i};
   >>     plot(pos(:,1), pos(:,2), 'LineWidth', 2);
   >> end
   >> xlabel('X Coordinate (m)');
   >> ylabel('Y Coordinate (m)');
   >> title('Vehicle Trajectories');
   >> grid on;

4. Or run the startup script:
   >> indian_traffic_matlab_demo

5. Or run generated analysis scripts:
   >> run('matlab_demo_scripts/indian_traffic_analysis_comprehensive_*.m');

The files contain:
- Vehicle trajectories with positions, velocities, and timestamps
- Road network with nodes, edges, and attributes  
- Traffic metrics including congestion and flow data
- All data is in MATLAB-native format for easy analysis
""")

if __name__ == "__main__":
    success = verify_matlab_files()
    show_matlab_usage()
    
    if success:
        print("\n✅ MATLAB integration is working correctly!")
        print("📁 Files are ready for use in MATLAB")
        print("📖 See MATLAB_INTEGRATION_GUIDE.md for detailed instructions")
    else:
        print("\n❌ Some issues found. Try running matlab_demo.py again.")