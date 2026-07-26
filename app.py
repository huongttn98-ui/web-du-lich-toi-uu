import streamlit as st
import itertools
import requests
import re

st.set_page_config(page_title="Hệ thống Tối ưu Tuyến đường Du lịch", page_icon="🗺️", layout="wide")

# ---------------------------------------------------------
# 1. KHO DỮ LIỆU ĐỊA ĐIỂM THAM QUAN
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
# 2. HÀM ĐỊNH VỊ ĐỊA CHỈ NHÀ RIÊNG THÔNG MINH (Hỗ trợ Tọa độ & Mapbox & Nominatim)
# ---------------------------------------------------------
def smart_geocode(input_str):
    if not input_str or not input_str.strip():
        return None
    
    clean_str = input_str.strip()
    
    # 1. TRƯỜNG HỢP A: Người dùng dán trực tiếp Tọa độ (Ví dụ: "10.6865, 106.5942" hoặc "10.6865 106.5942")
    coord_pattern = r'^(-?\d+\.\d+)[\s,]+(-?\d+\.\d+)$'
    match = re.match(coord_pattern, clean_str)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (lat, lon)

    # 2. TRƯỜNG HỢP B: Dùng Mapbox Geocoding API (Công khai miễn phí tìm địa chỉ nhà/hẻm tốt nhất)
    mapbox_token = "pk.eyJ1IjoibWFwYm94LWRlbW8iLCJhIjoiY2p4OTBsNGtwMDJhZDN5b2Nmd3V3dnE2OSJ9.R43s2oOvhg0T4a0Mv1K2mQ"
    mapbox_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(clean_str)}.json?access_token={mapbox_token}&country=vn&limit=1"
    
    try:
        res = requests.get(mapbox_url, timeout=4).json()
        if res.get("features"):
            coords = res["features"][0]["center"] # Mapbox trả về [lon, lat]
            return (coords[1], coords[0])
    except:
        pass

    # 3. TRƯỜNG HỢP C: Dự phòng bằng Nominatim
    search_query = clean_str if ("Vietnam" in clean_str or "Việt Nam" in clean_str) else f"{clean_str}, Việt Nam"
    nom_url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(search_query)}&format=json&limit=1"
    headers = {"User-Agent": "TourismApp_ResearchProject/2.0"}
    
    try:
        res = requests.get(nom_url, headers=headers, timeout=4).json()
        if res:
            return (float(res[0]["lat"]), float(res[0]["lon"]))
    except:
        pass

    return None

# ---------------------------------------------------------
# 3. HÀM TÍNH KHOẢNG CÁCH OSRM
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
# 4. GIAO DIỆN WEB
# ---------------------------------------------------------
st.title("🗺️ HỆ THỐNG TỐI ƯU HÓA TUYẾN ĐƯỜNG DU LỊCH")
st.caption("Cho phép tự nhập địa chỉ nhà riêng hoặc Tọa độ Google Maps")

col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.subheader("1. Thiết lập Hành trình")
    
    start_type = st.radio("Chọn phương thức nhập **ĐIỂM XUẤT PHÁT**:", ["Nhập Địa chỉ nhà / Tọa độ Google Maps", "Chọn từ danh sách địa điểm có sẵn"])
    
    start_name = ""
    start_coords = None
    
    if start_type == "Nhập Địa chỉ nhà / Tọa độ Google Maps":
        custom_input = st.text_input(
            "Nhập địa chỉ nhà hoặc Dán tọa độ Google Maps:", 
            value="10.6865, 106.5942",
            help="Ví dụ địa chỉ: 123 Đường Bến Lức, Bình Chánh, TP.HCM OR Dán tọa độ: 10.6865, 106.5942"
        )
        start_name = f"Điểm xuất phát ({custom_input})"
        
        if custom_input:
            with st.spinner("Đang định vị vị trí của bạn..."):
                start_coords = smart_geocode(custom_input)
                if start_coords:
                    st.success(f"📍 Đã định vị thành công! Tọa độ GPS: `{start_coords[0]:.4f}, {start_coords[1]:.4f}`")
                else:
                    st.error("❌ Không thể tìm thấy địa chỉ này. Bạn hãy thử dán Tọa độ GPS từ Google Maps nhé!")
    else:
        selected_start_poi = st.selectbox("Chọn điểm xuất phát:", list(POI_DATA.keys()))
        start_name = selected_start_poi
        start_coords = POI_DATA[selected_start_poi]["coords"]

    st.divider()
    all_poi_names = list(POI_DATA.keys())
    available_stops = [p for p in all_poi_names if p != start_name]
    
    selected_stops = st.multiselect("📌 Chọn các điểm tham quan bạn muốn ghé thăm:", available_stops, default=available_stops[:2])
    btn_calculate = st.button("🚀 TÌM LỘ TRÌNH TỐI ƯU NHẤT", type="primary", use_container_width=True)

with col_right:
    st.subheader("📸 Hình ảnh các điểm tham quan đã chọn")
    if not selected_stops:
        st.info("Vui lòng chọn ít nhất 1 địa điểm tham quan bên trái để xem hình ảnh.")
    else:
        for name in selected_stops:
            with st.container():
                st.markdown(f"#### 📍 {name}")
                st.image(POI_DATA[name]["image"], caption=name, use_container_width=True)
                st.caption(POI_DATA[name]["desc"])
                st.divider()

if btn_calculate:
    if not start_coords:
        st.error("Vui lòng kiểm tra lại Điểm xuất phát trước khi tính toán!")
    elif not selected_stops:
        st.warning("Vui lòng chọn ít nhất 1 địa điểm tham quan!")
    else:
        full_coords = [start_coords] + [POI_DATA[p]["coords"] for p in selected_stops]
        
        with st.spinner("Đang truy vấn dữ liệu bản đồ và tính toán tuyến đường ngắn nhất..."):
            dist_matrix = get_distance_matrix(full_coords)
            
            if dist_matrix:
                n = len(selected_stops)
                middle_indices = list(range(1, n + 1))
                
                best_dist = float('inf')
                best_order = []
                
                for perm in itertools.permutations(middle_indices):
                    current_order = [0] + list(perm) + [0]
                    current_dist = sum(dist_matrix[current_order[i]][current_order[i+1]] for i in range(len(current_order)-1))
                    
                    if current_dist < best_dist:
                        best_dist = current_dist
                        best_order = current_order
                
                st.success(f"✅ **ĐÃ TÌM THẤY LỘ TRÌNH TỐI ƯU!** | Tổng quãng đường: **{best_dist:.2f} km**")
                
                st.subheader("🚩 Thứ tự di chuyển đề xuất:")
                final_names = [start_name] + [selected_stops[i-1] for i in best_order[1:-1]] + [start_name]
                
                for idx, name in enumerate(final_names):
                    if idx == 0:
                        st.markdown(f"🚀 **Điểm xuất phát:** {name}")
                    elif idx == len(final_names) - 1:
                        st.markdown(f"🏁 **Kết thúc:** Quay về {name}")
                    else:
                        st.markdown(f"📍 **Chặng {idx}:** {name}")
                
                origin_str = f"{start_coords[0]},{start_coords[1]}"
                waypoints_str = "|".join([f"{POI_DATA[p]['coords'][0]},{POI_DATA[p]['coords'][1]}" for p in selected_stops])
                
                gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_str}&destination={origin_str}&waypoints={waypoints_str}&travelmode=driving"
                
                st.markdown(f"👉 **[BẤM VÀO ĐÂY ĐỂ MỞ DẪN ĐƯỜNG TRỰC TIẾP TRÊN GOOGLE MAPS]({gmaps_url})**")
