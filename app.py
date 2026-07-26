import streamlit as st
import itertools
import requests

st.set_page_config(page_title="Hệ thống Tối ưu Tuyến đường Du lịch", page_icon="🗺️", layout="wide")

# ---------------------------------------------------------
# 1. KHO DỮ LIỆU ĐỊA ĐIỂM (Bổ sung Ảnh & Tọa độ)
# ---------------------------------------------------------
POI_DATA = {
    "Khu di tích Lăng Le - Bàu Cò": {
        "coords": (10.7028, 106.5358),
        "desc": "Di tích lịch sử cấp Quốc gia, ghi dấu chiến công vang dội năm 1948.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Monument_placeholder.jpg/640px-Monument_placeholder.jpg" # Thay bằng link ảnh thực tế
    },
    "Chùa Phật Lớn (Bát Bửu Phật Đài)": {
        "coords": (10.7291, 106.5297),
        "desc": "Nơi thờ tượng Phật Thích Ca cao 7m uy nghiêm, không gian thanh tĩnh.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Pagoda_placeholder.jpg/640px-Pagoda_placeholder.jpg"
    },
    "Di tích Dân công hỏa tuyến Mậu Thân": {
        "coords": (10.7150, 106.5410),
        "desc": "Nơi tưởng niệm sự hy sinh anh dũng của 32 nữ dân công hỏa tuyến năm 1968.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Monument_placeholder.jpg/640px-Monument_placeholder.jpg"
    },
    "Dinh Độc Lập": {
        "coords": (10.7769, 106.6953),
        "desc": "Di tích quốc gia đặc biệt, biểu tượng lịch sử ngày thống nhất đất nước 30/04/1975.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Independence_Palace_Saigon.jpg/640px-Independence_Palace_Saigon.jpg"
    },
    "Bến Nhà Rồng": {
        "coords": (10.7681, 106.7068),
        "desc": "Bảo tàng Hồ Chí Minh – nơi Bác Hồ ra đi tìm đường cứu nước năm 1911.",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Ho_Chi_Minh_Museum_Saigon.jpg/640px-Ho_Chi_Minh_Museum_Saigon.jpg"
    }
}

# ---------------------------------------------------------
# 2. HÀM TÍNH KHOẢNG CÁCH API
# ---------------------------------------------------------
def get_distance_matrix(coords_list):
    n = len(coords_list)
    coords_str = ";".join([f"{lon},{lat}" for lat, lon in coords_list])
    url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=distance"
    try:
        res = requests.get(url, timeout=5).json()
        distances = res.get("distances", [])
        return [[round(distances[i][j] / 1000.0, 2) for j in range(n)] for i in range(n)]
    except:
        return None

# ---------------------------------------------------------
# 3. GIAO DIỆN WEB CẢI TIẾN
# ---------------------------------------------------------
st.title("🗺️ HỆ THỐNG TỐI ƯU HÓA TUYẾN ĐƯỜNG DU LỊCH")
st.caption("Cho phép tùy chọn Điểm Đầu & Điểm Cuối - Tích hợp Hình ảnh & Bản đồ Tương tác")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("1. Thiết lập Hành trình")
    
    # Cho phép người dùng tùy chọn điểm bắt đầu và điểm kết thúc
    all_poi_names = list(POI_DATA.keys())
    
    start_point = st.selectbox("📍 Chọn **ĐIỂM XUẤT PHÁT**:", all_poi_names, index=0)
    end_point = st.selectbox("🏁 Chọn **ĐIỂM KẾT THÚC**:", all_poi_names, index=len(all_poi_names)-1)
    
    # Lựa chọn các điểm tham quan trung gian
    available_stops = [p for p in all_poi_names if p != start_point and p != end_point]
    selected_stops = st.multiselect("📌 Chọn các điểm tham quan trên đường đi:", available_stops, default=available_stops[:2])
    
    btn_calculate = st.button("🚀 TÌM LỘ TRÌNH TỐI ƯU NHẤT", type="primary", use_container_width=True)

with col_right:
    st.subheader("📸 Hình ảnh & Thông tin Địa điểm đã chọn")
    current_selected = list(set([start_point, end_point] + selected_stops))
    
    # Hiển thị dạng thẻ Carousel/Grid có ảnh
    grid_cols = st.columns(2)
    for idx, name in enumerate(current_selected):
        with grid_cols[idx % 2]:
            st.image(POI_DATA[name]["image"], caption=name, use_container_width=True)
            st.caption(POI_DATA[name]["desc"])

# XỬ LÝ TÍNH TOÁN KHI BẤM NÚT
if btn_calculate:
    # Lập danh sách thứ tự: [Điểm đầu] + [Các điểm trung gian] + [Điểm cuối]
    full_route_nodes = [start_point] + selected_stops + [end_point]
    full_coords = [POI_DATA[p]["coords"] for p in full_route_nodes]
    
    with st.spinner("Đang truy vấn dữ liệu bản đồ và tối ưu tuyến đường..."):
        dist_matrix = get_distance_matrix(full_coords)
        
        if dist_matrix:
            n = len(full_route_nodes)
            middle_indices = list(range(1, n - 1)) # Các điểm trung gian
            
            best_dist = float('inf')
            best_order = []
            
            # Vét cạn các hoán vị của điểm trung gian (Giữ cố định Đỉnh đầu index 0 và Đỉnh cuối index n-1)
            for perm in itertools.permutations(middle_indices):
                current_order = [0] + list(perm) + [n - 1]
                current_dist = sum(dist_matrix[current_order[i]][current_order[i+1]] for i in range(len(current_order)-1))
                
                if current_dist < best_dist:
                    best_dist = current_dist
                    best_order = current_order
            
            st.divider()
            st.success(f"✅ **ĐÃ TÌM THẤY LỘ TRÌNH TỐI ƯU!** | Tổng quãng đường: **{best_dist:.2f} km**")
            
            # Hiển thị lộ trình
            st.subheader("🚩 Thứ tự di chuyển đề xuất:")
            final_route_names = [full_route_nodes[i] for i in best_order]
            
            for idx, name in enumerate(final_route_names):
                if idx == 0:
                    st.markdown(f"🚀 **Điểm xuất phát:** {name}")
                elif idx == len(final_route_names) - 1:
                    st.markdown(f"🏁 **Điểm kết thúc:** {name}")
                else:
                    st.markdown(f"📍 **Chặng {idx}:** {name}")
            
            # NHÚNG BẢN ĐỒ GOOGLE MAPS TƯƠNG TÁC LÊN WEB
            # Tạo đường link chỉ đường Google Maps Directions động
            origin_coords = f"{POI_DATA[start_point]['coords'][0]},{POI_DATA[start_point]['coords'][1]}"
            destination_coords = f"{POI_DATA[end_point]['coords'][0]},{POI_DATA[end_point]['coords'][1]}"
            
            waypoints = "|".join([f"{POI_DATA[final_route_names[i]]['coords'][0]},{POI_DATA[final_route_names[i]]['coords'][1]}" for i in range(1, len(final_route_names)-1)])
            
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_coords}&destination={destination_coords}&waypoints={waypoints}&travelmode=driving"
            
            st.markdown(f"👉 **[BẤM VÀO ĐÂY ĐỂ MỞ BẢN ĐỒ DẪN ĐƯỜNG TRỰC TIẾP TRÊN GOOGLE MAPS]({gmaps_url})**")
