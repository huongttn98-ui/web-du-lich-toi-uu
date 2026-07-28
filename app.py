import streamlit as st
import itertools
import requests
import re
import folium
from streamlit_folium import st_folium

# ---------------------------------------------------------
# 0. CẤU HÌNH TRANG & THIẾT LẬP SESSION STATE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cẩm Nang & Tối Ưu Tuyến Đường Du Lịch TP.HCM", 
    page_icon="🗺️", 
    layout="wide"
)

# 1. Khởi tạo danh sách địa điểm chọn từ Cẩm nang
if "selected_places" not in st.session_state:
    st.session_state["selected_places"] = [
        "Dinh Độc Lập, Quận 1",
        "Chợ Bến Thành, Quận 1",
        "Chùa Bát Bửu Phật Đài, Bình Chánh"
    ]

# 2. KHÓA LƯU KẾT QUẢ TÍNH TOÁN (Chống biến mất khi rerun)
if "calculation_result" not in st.session_state:
    st.session_state["calculation_result"] = None

def add_place_to_list(place_name):
    """Hàm xử lý khi bấm nút '➕ Chọn điểm này' từ Cẩm nang"""
    if place_name not in st.session_state["selected_places"]:
        st.session_state["selected_places"].append(place_name)
        st.toast(f"✅ Đã thêm '{place_name}' vào danh sách!", icon="📍")
    else:
        st.toast(f"⚠️ '{place_name}' đã có trong danh sách!", icon="ℹ️")

# ---------------------------------------------------------
# 1. HÀM CHUYỂN ĐỔI TỌA ĐỘ THÔNG MINH (SMART GEOCODING)
# ---------------------------------------------------------
def smart_geocode(input_str):
    if not input_str or not input_str.strip():
        return None
    clean_str = input_str.strip()
    
    # 1. Link Google Maps
    gmaps_link_pattern = r'@(-?\d+\.\d+),(-?\d+\.\d+)'
    gmaps_match = re.search(gmaps_link_pattern, clean_str)
    if gmaps_match:
        return (round(float(gmaps_match.group(1)), 6), round(float(gmaps_match.group(2)), 6))

    # 2. Tọa độ GPS trực tiếp
    coord_pattern = r'^(-?\d+\.\d+)[\s,]+(-?\d+\.\d+)$'
    match = re.match(coord_pattern, clean_str)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (round(lat, 6), round(lon, 6))

    # 3. OpenStreetMap Nominatim
    search_query = clean_str.split(',')[0].strip()
    search_text_full = f"{clean_str}, Hồ Chí Minh, Việt Nam" if "Hồ Chí Minh" not in clean_str else clean_str

    for query in [search_text_full, search_query]:
        nom_url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&limit=1"
        headers = {"User-Agent": "TourismRouteOptimizerApp/7.0"}
        try:
            res = requests.get(nom_url, headers=headers, timeout=4).json()
            if res and len(res) > 0:
                return (round(float(res[0]["lat"]), 6), round(float(res[0]["lon"]), 6))
        except:
            pass

    return None

# ---------------------------------------------------------
# 2. HÀM LẤY GIỚI THIỆU & HÌNH ẢNH TỪ WIKIPEDIA API
# ---------------------------------------------------------
def get_place_info_wikipedia(place_name):
    clean_name = place_name.split(',')[0].strip()
    wiki_search_url = f"https://vi.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(clean_name)}&format=json"
    
    try:
        headers = {"User-Agent": "TourismRouteOptimizerApp/7.0"}
        search_res = requests.get(wiki_search_url, headers=headers, timeout=3).json()
        search_results = search_res.get("query", {}).get("search", [])
        
        if search_results:
            page_title = search_results[0]["title"]
            summary_url = f"https://vi.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(page_title)}"
            summary_res = requests.get(summary_url, headers=headers, timeout=3).json()
            
            description = summary_res.get("extract", "Địa điểm tham quan hấp dẫn trong hành trình du lịch.")
            image_url = summary_res.get("thumbnail", {}).get("source", None)
            
            return {
                "title": page_title,
                "description": description if len(description) <= 250 else description[:250] + "...",
                "image_url": image_url
            }
    except:
        pass
        
    return {
        "title": clean_name,
        "description": "Địa điểm tham quan hấp dẫn trong hành trình du lịch.",
        "image_url": "https://images.unsplash.com/photo-1503220317375-aaad61436b1b?auto=format&fit=crop&w=600&q=80"
    }

# =========================================================
# PHẦN A: CẨM NANG DU LỊCH & KHÁM PHÁ TP.HCM (GIAO DIỆN PHÍA TRÊN)
# =========================================================
st.title("🏙️ Cẩm Nang Du Lịch & Khám Phá TP. Hồ Chí Minh")
st.caption("Khám phá danh thắng nổi tiếng và bấm chọn trực tiếp để lập lộ trình di chuyển tối ưu nhất")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏛️ Di Tích & Lịch Sử", 
    "🛕 Tâm Linh & Văn Hóa", 
    "🌳 Giải Trí & Sinh Thái", 
    "📍 Khám Phá Bình Chánh"
])

# ---- TAB 1 ----
with tab1:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Reunification_Palace_Saigon.jpg/640px-Reunification_Palace_Saigon.jpg", use_column_width=True)
        st.markdown("### Dinh Độc Lập")
        st.caption("📍 Tọa độ: `10.7769, 106.6953` | Quận 1")
        st.write("Di tích lịch sử quốc gia đặc biệt, nơi chứng kiến thời khắc giải phóng miền Nam 30/4/1975.")
        if st.button("➕ Chọn điểm này", key="btn_dinh_doc_lap"):
            add_place_to_list("Dinh Độc Lập, Quận 1")

    with c2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Cho_Ben_Thanh.jpg/640px-Cho_Ben_Thanh.jpg", use_column_width=True)
        st.markdown("### Chợ Bến Thành")
        st.caption("📍 Tọa độ: `10.7725, 106.6980` | Quận 1")
        st.write("Biểu tượng văn hóa lâu đời của TP.HCM, nơi giao thương sầm uất với vô số ẩm thực đặc sản.")
        if st.button("➕ Chọn điểm này", key="btn_ben_thanh"):
            add_place_to_list("Chợ Bến Thành, Quận 1")

    with c3:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Ben_Nha_Rong_2019.jpg/640px-Ben_Nha_Rong_2019.jpg", use_column_width=True)
        st.markdown("### Bến Nhà Rồng")
        st.caption("📍 Tọa độ: `10.7682, 106.7068` | Quận 4")
        st.write("Bảo tàng Hồ Chí Minh, nơi Bác Hồ ra đi tìm đường cứu nước năm 1911 bên sông Sài Gòn.")
        if st.button("➕ Chọn điểm này", key="btn_ben_nha_rong"):
            add_place_to_list("Bến Nhà Rồng, Quận 4")

# ---- TAB 2 ----
with tab2:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Saigon_Notre-Dame_Cathedral_2019.jpg/640px-Saigon_Notre-Dame_Cathedral_2019.jpg", use_column_width=True)
        st.markdown("### Nhà Thờ Đức Bà")
        st.caption("📍 Tọa độ: `10.7798, 106.6990` | Quận 1")
        st.write("Tuyệt tác kiến trúc Roman kết hợp Gothic cổ kính ngay tại trung tâm thành phố.")
        if st.button("➕ Chọn điểm này", key="btn_duc_ba"):
            add_place_to_list("Nhà Thờ Đức Bà, Quận 1")

    with c2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Chua_Vinh_Nghiem_Saigon.jpg/640px-Chua_Vinh_Nghiem_Saigon.jpg", use_column_width=True)
        st.markdown("### Chùa Vĩnh Nghiêm")
        st.caption("📍 Tọa độ: `10.7915, 106.6821` | Quận 3")
        st.write("Ngôi chùa nổi tiếng với tháp đá đồ sộ, không gian thanh tịnh giữa lòng đô thị.")
        if st.button("➕ Chọn điểm này", key="btn_vinh_nghiem"):
            add_place_to_list("Chùa Vĩnh Nghiêm, Quận 3")

    with c3:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Chua_Bat_Buu_Phat_Dai.jpg/640px-Chua_Bat_Buu_Phat_Dai.jpg", use_column_width=True)
        st.markdown("### Chùa Bát Bửu Phật Đài")
        st.caption("📍 Tọa độ: `10.7291, 106.5297` | Bình Chánh")
        st.write("Địa điểm tâm linh nổi tiếng thanh bình tại Bình Chánh, còn gọi là Chùa Phật Cô Đơn.")
        if st.button("➕ Chọn điểm này", key="btn_phat_co_don"):
            add_place_to_list("Chùa Bát Bửu Phật Đài, Bình Chánh")

# ---- TAB 3 ----
with tab3:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Dam_Sen_Park.jpg/640px-Dam_Sen_Park.jpg", use_column_width=True)
        st.markdown("### Công Viên Đầm Sen")
        st.caption("📍 Tọa độ: `10.7684, 106.6453` | Quận 11")
        st.write("Khu vui chơi giải trí phức hợp lớn với nhiều trò chơi cảm giác mạnh và công viên nước.")
        if st.button("➕ Chọn điểm này", key="btn_dam_sen"):
            add_place_to_list("Công viên Đầm Sen, Quận 11")

    with c2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Thao_Cam_Vien_Saigon.jpg/640px-Thao_Cam_Vien_Saigon.jpg", use_column_width=True)
        st.markdown("### Thảo Cầm Viên")
        st.caption("📍 Tọa độ: `10.7875, 106.7053` | Quận 1")
        st.write("Lá phổi xanh trung tâm thành phố, bảo tồn hàng ngàn động thực vật quý hiếm.")
        if st.button("➕ Chọn điểm này", key="btn_thao_cam_vien"):
            add_place_to_list("Thảo Cầm Viên, Quận 1")

    with c3:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Suoi_Tien_Theme_Park.jpg/640px-Suoi_Tien_Theme_Park.jpg", use_column_width=True)
        st.markdown("### KDL Suối Tiên")
        st.caption("📍 Tọa độ: `10.8631, 106.8028` | TP. Thủ Đức")
        st.write("Khu du lịch văn hóa chủ đề lồng ghép các truyền thuyết lịch sử, dân gian Việt Nam.")
        if st.button("➕ Chọn điểm này", key="btn_suoi_tien"):
            add_place_to_list("Khu du lịch Suối Tiên, TP. Thủ Đức")

# ---- TAB 4 ----
with tab4:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Chua_Bat_Buu_Phat_Dai.jpg/640px-Chua_Bat_Buu_Phat_Dai.jpg", use_column_width=True)
        st.markdown("### Bát Bửu Phật Đài")
        st.caption("📍 Tọa độ: `10.7291, 106.5297` | Lê Minh Xuân")
        st.write("Di tích kiến trúc tôn giáo nổi tiếng tại xã Lê Minh Xuân, huyện Bình Chánh.")
        if st.button("➕ Chọn điểm này", key="btn_bc_1"):
            add_place_to_list("Chùa Bát Bửu Phật Đài, Bình Chánh")

    with c2:
        st.image("https://images.unsplash.com/photo-1503220317375-aaad61436b1b?auto=format&fit=crop&w=600&q=80", use_column_width=True)
        st.markdown("### Di Tích Lăng Le - Bàu Cò")
        st.caption("📍 Tọa độ: `10.7385, 106.5123` | Tân Nhựt")
        st.write("Di tích lịch sử cách mạng địa phương, ghi dấu những chiến công anh hùng tại Bình Chánh.")
        if st.button("➕ Chọn điểm này", key="btn_bc_2"):
            add_place_to_list("Khu di tích Lăng Le Bàu Cò, Bình Chánh")

    with c3:
        st.image("https://images.unsplash.com/photo-1511497584788-8767611136f6?auto=format&fit=crop&w=600&q=80", use_column_width=True)
        st.markdown("### Dân Công Hỏa Tuyến")
        st.caption("📍 Tọa độ: `10.7012, 106.5411` | Vĩnh Lộc A")
        st.write("Nơi tưởng niệm sự hy sinh anh dũng của các nữ dân công hỏa tuyến Mậu Thân 1968.")
        if st.button("➕ Chọn điểm này", key="btn_bc_3"):
            add_place_to_list("Di tích Dân Công Hỏa Tuyến, Bình Chánh")

st.divider()

# =========================================================
# PHẦN B: CÔNG CỤ TỐI ƯU LỘ TRÌNH (GIAO DIỆN PHÍA DƯỚI)
# =========================================================
st.subheader("🛠️ Công Cụ Lập Kế Hoạch & Tối Ưu Lộ Trình Di Chuyển")
st.caption("Ứng dụng thuật toán Vét cạn (Brute Force / TSP) & Mạng lưới Giao thông Đường bộ OSRM")

st.sidebar.header("📍 Cấu hình Lộ trình")

start_input = st.sidebar.text_input(
    "1. Điểm xuất phát (Địa chỉ/GPS/Link Maps):",
    value="10.6865, 106.5942",
    help="Nhập tọa độ, tên địa chỉ hoặc dán Link Google Maps"
)

current_list = st.session_state["selected_places"]
num_destinations = st.sidebar.number_input(
    "2. Số lượng điểm tham quan:",
    min_value=2,
    max_value=12,
    value=max(2, len(current_list)),
    step=1
)

st.sidebar.subheader("3. Danh sách điểm chọn:")
destination_inputs = []

for i in range(num_destinations):
    default_val = current_list[i] if i < len(current_list) else ""
    dest_str = st.sidebar.text_input(f"Địa điểm {i+1}:", value=default_val, key=f"dest_input_{i}")
    destination_inputs.append(dest_str)

# ---------------------------------------------------------
# XỬ LÝ TÍNH TOÁN VÀ LƯU VÀO SESSION STATE
# ---------------------------------------------------------
if st.sidebar.button("🚀 Bắt đầu tối ưu tuyến đường", type="primary"):
    with st.spinner("Đang tính toán lộ trình giao thông thực tế và thu thập thông tin..."):
        
        start_coords = smart_geocode(start_input)
        if not start_coords:
            st.error("❌ Không thể xác định vị trí Điểm xuất phát. Vui lòng kiểm tra lại nhập liệu!")
            st.stop()
            
        valid_points = [("Điểm xuất phát", start_coords)]
        geocode_table = [{"Mục": "Xuất phát", "Địa điểm nhập": start_input, "Tọa độ GPS": f"{start_coords[0]}, {start_coords[1]}"}]
        places_info = {}
        has_error = False

        for i, dest_text in enumerate(destination_inputs):
            if not dest_text.strip():
                continue
            coords = smart_geocode(dest_text)
            if coords:
                valid_points.append((dest_text.strip(), coords))
                geocode_table.append({"Mục": f"Điểm {i+1}", "Địa điểm nhập": dest_text, "Tọa độ GPS": f"{coords[0]}, {coords[1]}"})
                places_info[dest_text.strip()] = get_place_info_wikipedia(dest_text.strip())
            else:
                st.error(f"❌ Không tìm thấy tọa độ cho: '{dest_text}'")
                has_error = True

        if has_error or len(valid_points) - 1 < 2:
            st.warning("⚠️ Cần ít nhất 2 địa điểm tham quan hợp lệ để tiến hành tối ưu.")
            st.stop()

        # Gọi API OSRM
        coords_str = ";".join([f"{lon},{lat}" for name, (lat, lon) in valid_points])
        osrm_table_url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=distance"
        
        try:
            res_table = requests.get(osrm_table_url, timeout=6).json()
            if "distances" in res_table:
                matrix = [[round(d / 1000.0, 2) for d in row] for row in res_table["distances"]]
                
                num_targets = len(valid_points) - 1
                target_indices = list(range(1, num_targets + 1))
                
                best_dist = float('inf')
                best_path = []
                
                for perm in itertools.permutations(target_indices):
                    current_path = [0] + list(perm) + [0]
                    current_dist = sum(matrix[current_path[i]][current_path[i+1]] for i in range(len(current_path)-1))
                    
                    if current_dist < best_dist:
                        best_dist = current_dist
                        best_path = current_path
                
                # Gọi OSRM Route API vẽ đường uốn lượn
                ordered_points = [valid_points[idx] for idx in best_path]
                route_coords_str = ";".join([f"{lon},{lat}" for name, (lat, lon) in ordered_points])
                osrm_route_url = f"http://router.project-osrm.org/route/v1/driving/{route_coords_str}?overview=full&geometries=geojson"
                
                res_route = requests.get(osrm_route_url, timeout=6).json()
                folium_line = []
                if "routes" in res_route and len(res_route["routes"]) > 0:
                    geometry = res_route["routes"][0]["geometry"]["coordinates"]
                    folium_line = [[lat, lon] for lon, lat in geometry]

                # LƯU TOÀN BỘ KẾT QUẢ VÀO SESSION STATE
                st.session_state["calculation_result"] = {
                    "geocode_table": geocode_table,
                    "best_dist": best_dist,
                    "ordered_points": ordered_points,
                    "places_info": places_info,
                    "folium_line": folium_line,
                    "start_coords": start_coords
                }

        except Exception as e:
            st.error(f"Xảy ra lỗi kết nối OSRM: {e}")

# =========================================================
# HIỂN THỊ KẾT QUẢ (NẾU ĐÃ CÓ TRONG SESSION STATE)
# =========================================================
if st.session_state["calculation_result"] is not None:
    res = st.session_state["calculation_result"]
    
    st.markdown("#### 📌 Tọa độ GPS các điểm đã xác định thành công:")
    st.dataframe(res["geocode_table"], use_container_width=True)

    st.success(f"🎉 **Đã tìm ra lộ trình ngắn nhất!** Tổng quãng đường lái xe thực tế: **{round(res['best_dist'], 2)} km**")
    
    # 1. Liệt kê thứ tự & Link Google Maps
    st.markdown("### 📋 Thứ tự di chuyển tối ưu đề xuất:")
    gmaps_coords = []
    for step, (name, coords) in enumerate(res["ordered_points"]):
        gmaps_coords.append(f"{coords[0]},{coords[1]}")
        if step == 0:
            st.write(f"🚩 **Khởi hành:** {name} *(Tọa độ: {coords[0]}, {coords[1]})*")
        elif step == len(res["ordered_points"]) - 1:
            st.write(f"🏁 **Kết thúc:** Trở về Điểm xuất phát")
        else:
            st.write(f"🔹 **Thứ tự {step}:** {name} *(Tọa độ: {coords[0]}, {coords[1]})*")

    gmaps_url = f"https://www.google.com/maps/dir/{'/'.join(gmaps_coords)}"
    st.markdown(f"🔗 **[👉 Mở lộ trình di chuyển này trên ứng dụng Google Maps Navigation]({gmaps_url})**")

    # 2. Thông tin & Ảnh Wikipedia
    st.divider()
    st.markdown("### 🏛️ Hình ảnh & Giới thiệu chi tiết các điểm trong lộ trình")
    
    col_list = st.columns(min(len(res["ordered_points"]) - 2, 3))
    c_idx = 0
    
    for step, (name, coords) in enumerate(res["ordered_points"][1:-1], 1):
        info = res["places_info"].get(name, {
            "title": name, 
            "description": "Địa điểm tham quan du lịch.", 
            "image_url": "https://images.unsplash.com/photo-1503220317375-aaad61436b1b?auto=format&fit=crop&w=600&q=80"
        })
        
        with col_list[c_idx % len(col_list)]:
            st.markdown(f"#### {step}. {info['title']}")
            if info.get("image_url"):
                st.image(info["image_url"], use_column_width=True)
            st.caption(f"📍 Tọa độ: {coords[0]}, {coords[1]}")
            st.write(info["description"])
            st.write("---")
        c_idx += 1

    # 3. Bản đồ Folium
    st.divider()
    st.markdown("### 🗺️ Bản đồ mô phỏng đường đi thực tế (OSRM Route)")
    st.caption("Tuyến đường màu xanh navy thể hiện chi tiết luồng giao thông thực tế bám sát hạ tầng đường bộ.")

    m = folium.Map(location=res["start_coords"], zoom_start=12, tiles="OpenStreetMap")
    
    for step, (name, coords) in enumerate(res["ordered_points"][:-1]):
        icon_color = "red" if step == 0 else "blue"
        popup_text = f"Xuất phát: {name}" if step == 0 else f"Thứ tự {step}: {name}"
        folium.Marker(
            location=coords,
            popup=popup_text,
            tooltip=f"{step}. {name}",
            icon=folium.Icon(color=icon_color, icon="info-sign" if step != 0 else "home")
        ).add_to(m)

    if res["folium_line"]:
        folium.PolyLine(
            res["folium_line"],
            color="#1A365D",
            weight=5,
            opacity=0.85,
            dash_array='8',
            tooltip="Tuyến đường thực tế"
        ).add_to(m)

    st_folium(m, width=1100, height=500)
