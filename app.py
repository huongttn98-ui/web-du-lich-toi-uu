import streamlit as st
import itertools
import requests

st.set_page_config(page_title="Hệ thống Tối ưu Tuyến đường Du lịch", page_icon="🗺️", layout="wide")

# ---------------------------------------------------------
# 1. KHO DỮ LIỆU ĐỊA ĐIỂM THAM QUAN (Đã cập nhật Link ảnh trực tiếp)
# ---------------------------------------------------------
POI_DATA = {
    "Khu di tích Lăng Le - Bàu Cò": {
        "coords": (10.7028, 106.5358),
        "desc": "Di tích lịch sử cấp Quốc gia, ghi dấu chiến công vang dội năm 1948.",
        "image": "https://images.unsplash.com/photo-1509114397022-ed747cca3f65?w=600"
    },
    "Chùa Phật Lớn (Bát Bửu Phật Đài)": {
        "coords": (10.7291, 106.5297),
        "desc": "Nơi thờ tượng Phật Thích Ca cao 7m uy nghiêm, không gian thanh tĩnh.",
        "image": "https://images.unsplash.com/photo-1542640244-7e672d6cef21?w=600"
    },
    "Di tích Dân công hỏa tuyến Mậu Thân": {
        "coords": (10.7150, 106.5410),
        "desc": "Nơi tưởng niệm sự hy sinh anh dũng của 32 nữ dân công hỏa tuyến năm 1968.",
        "image": "https://images.unsplash.com/photo-1590059206170-661f433a0e88?w=600"
    },
    "Dinh Độc Lập": {
        "coords": (10.7769, 106.6953),
        "desc": "Di tích quốc gia đặc biệt, biểu tượng lịch sử ngày thống nhất đất nước 30/04/1975.",
        "image": "https://images.unsplash.com/photo-1583417319070-4a69db38a482?w=600"
    },
    "Bến Nhà Rồng": {
        "coords": (10.7681, 106.7068),
        "desc": "Bảo tàng Hồ Chí Minh – nơi Bác Hồ ra đi tìm đường cứu nước năm 1911.",
        "image": "https://images.unsplash.com/photo-1508873696983-2df515122519?w=600"
    }
}

# ---------------------------------------------------------
# 2. HÀM TỰ ĐỘNG ĐỔI ĐỊA CHỈ TỰ ĐIỀN THÀNH TỌA ĐỘ GPS (Nominatim API)
# ---------------------------------------------------------
def get_coords_from_address(address_str):
    # 1. Kiểm tra nếu người dùng dán trực tiếp Tọa độ (Ví dụ: 10.6865, 106.5942)
    try:
        parts = address_str.split(',')
        if len(parts) == 2:
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
    except:
        pass

    # 2. Nếu là chuỗi địa chỉ, thêm ", Vietnam" để API dễ định vị hơn
    search_query = address_str if "Vietnam" in address_str or "Việt Nam" in address_str else f"{address_str}, Vietnam"
    url = f"https://nominatim.openstreetmap.org/search?q={search_query}&format=json&limit=1"
    headers = {"User-Agent": "TourismApp_ResearchProject/1.0 (contact@school.edu.vn)"}
    
    try:
        res = requests.get(url, headers=headers, timeout=5).json()
        if res:
            return (float(res[0]["lat"]), float(res[0]["lon"]))
    except Exception as e:
        pass
    return None

# ---------------------------------------------------------
# 3. HÀM TÍNH KHOẢNG CÁCH QUA OSRM API
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
# 4. GIAO DIỆN WEB CẢI TIẾN
# ---------------------------------------------------------
st.title("🗺️ HỆ THỐNG TỐI ƯU HÓA TUYẾN ĐƯỜNG DU LỊCH")
st.caption("Cho phép người dùng tự nhập địa điểm xuất phát bất kỳ - Tích hợp hình ảnh trực quan")

col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.subheader("1. Thiết lập Hành trình")
    
    # MỤC 1: CHO PHÉP TỰ NHẬP ĐỊA ĐIỂM BẮT ĐẦU TỰ DO
    start_type = st.radio("Lựa chọn phương thức nhập **ĐIỂM XUẤT PHÁT**:", ["Chọn từ danh sách có sẵn", "Tự nhập địa chỉ/tên vị trí bất kỳ"])
    
    start_name = ""
    start_coords = None
    
    if start_type == "Tự nhập địa chỉ/tên vị trí bất kỳ":
        custom_input = st.text_input("Nhập địa chỉ hoặc tên vị trí của bạn (VD: Trường THPT Bình Chánh, TP.HCM):", "Trường THPT Bình Chánh, TP.HCM")
        start_name = f"Vị trí tự chọn ({custom_input})"
        if custom_input:
            with st.spinner("Đang định vị địa chỉ của bạn..."):
                start_coords = get_coords_from_address(custom_input)
                if start_coords:
                    st.caption(f"📍 Đã tìm thấy tọa độ GPS: `{start_coords[0]:.4f}, {start_coords[1]:.4f}`")
                else:
                    st.warning("⚠️ Không tìm thấy tọa độ chính xác. Hệ thống sẽ tạm lấy vị trí trung tâm TP.HCM.")
                    start_coords = (10.7769, 106.7009)
    else:
        selected_start_poi = st.selectbox("Chọn điểm xuất phát:", list(POI_DATA.keys()))
        start_name = selected_start_poi
        start_coords = POI_DATA[selected_start_poi]["coords"]

    # MỤC 2: CHỌN CÁC ĐỊA ĐIỂM THAM QUAN
    st.divider()
    all_poi_names = list(POI_DATA.keys())
    available_stops = [p for p in all_poi_names if p != start_name]
    
    selected_stops = st.multiselect("📌 Chọn các điểm tham quan bạn muốn ghé thăm:", available_stops, default=available_stops[:2])
    
    btn_calculate = st.button("🚀 TÌM LỘ TRÌNH TỐI ƯU NHẤT", type="primary", use_container_width=True)

# HIỂN THỊ HÌNH ẢNH Ở CỘT BÊN PHẢI
with col_right:
    st.subheader("📸 Hình ảnh các điểm tham quan đã chọn")
    if not selected_stops:
        st.info("Vui lòng chọn ít nhất 1 địa điểm tham quan bên trái để xem hình ảnh.")
    else:
        for name in selected_stops:
            with st.container():
                st.markdown(f"#### 📍 {name}")
                # Hiển thị ảnh trực tiếp
                st.image(POI_DATA[name]["image"], caption=name, use_container_width=True)
                st.caption(POI_DATA[name]["desc"])
                st.divider()

# XỬ LÝ TÍNH TOÁN LỘ TRÌNH
if btn_calculate:
    if not selected_stops:
        st.warning("Vui lòng chọn ít nhất 1 địa điểm tham quan!")
    else:
        full_route_names = [start_name] + selected_stops + [start_name] # Xuất phát -> Đi tham quan -> Quay về điểm xuất phát
        full_coords = [start_coords] + [POI_DATA[p]["coords"] for p in selected_stops] + [start_coords]
        
        with st.spinner("Đang truy vấn dữ liệu bản đồ và tối ưu tuyến đường..."):
            dist_matrix = get_distance_matrix(full_coords[:-1]) # Tính ma trận cho các đỉnh phân biệt
            
            if dist_matrix:
                n = len(selected_stops)
                middle_indices = list(range(1, n + 1))
                
                best_dist = float('inf')
                best_order = []
                
                # Tìm hoán vị tối ưu
                for perm in itertools.permutations(middle_indices):
                    current_order = [0] + list(perm) + [0]
                    current_dist = sum(dist_matrix[current_order[i]][current_order[i+1]] for i in range(len(current_order)-1))
                    
                    if current_dist < best_dist:
                        best_dist = current_dist
                        best_order = current_order
                
                st.success(f"✅ **ĐÃ TÌM THẤY LỘ TRÌNH TỐI ƯU!** | Tổng quãng đường: **{best_dist:.2f} km**")
                
                # In thứ tự di chuyển
                st.subheader("🚩 Thứ tự di chuyển đề xuất:")
                final_names = [start_name] + [selected_stops[i-1] for i in best_order[1:-1]] + [start_name]
                
                for idx, name in enumerate(final_names):
                    if idx == 0:
                        st.markdown(f"🚀 **Điểm xuất phát:** {name}")
                    elif idx == len(final_names) - 1:
                        st.markdown(f"🏁 **Kết thúc:** Quay về {name}")
                    else:
                        st.markdown(f"📍 **Chặng {idx}:** {name}")
                
                # TẠO LINK CHỈ ĐƯỜNG TRÊN GOOGLE MAPS
                origin_str = f"{start_coords[0]},{start_coords[1]}"
                waypoints_str = "|".join([f"{POI_DATA[p]['coords'][0]},{POI_DATA[p]['coords'][1]}" for p in selected_stops])
                
                gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_str}&destination={origin_str}&waypoints={waypoints_str}&travelmode=driving"
                
                st.markdown(f"👉 **[BẤM VÀO ĐÂY ĐỂ MỞ DẪN ĐƯỜNG TRỰC TIẾP TRÊN GOOGLE MAPS]({gmaps_url})**")
