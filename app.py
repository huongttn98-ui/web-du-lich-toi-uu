import streamlit as st
import itertools
import requests
import re
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Tối ưu lộ trình du lịch thực tế", page_icon="🗺️", layout="wide")

# ---------------------------------------------------------
# 1. HÀM CHUYỂN ĐỔI ĐỊA CHỈ / TỌA ĐỘ THÔNG MINH (SMART GEOCODING)
# ---------------------------------------------------------
def smart_geocode(input_str):
    if not input_str or not input_str.strip():
        return None
    clean_str = input_str.strip()
    
    # Ưu tiên 1: Người dùng dán Link Google Maps (Bắt chuỗi dạng @lat,lon)
    gmaps_link_pattern = r'@(-?\d+\.\d+),(-?\d+\.\d+)'
    gmaps_match = re.search(gmaps_link_pattern, clean_str)
    if gmaps_match:
        lat = round(float(gmaps_match.group(1)), 6)
        lon = round(float(gmaps_match.group(2)), 6)
        return (lat, lon)

    # Ưu tiên 2: Người dùng dán trực tiếp Tọa độ GPS (VD: 10.7769, 106.6953)
    coord_pattern = r'^(-?\d+\.\d+)[\s,]+(-?\d+\.\d+)$'
    match = re.match(coord_pattern, clean_str)
    if match:
        lat = round(float(match.group(1)), 6)
        lon = round(float(match.group(2)), 6)
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (lat, lon)

    # Ưu tiên 3: Tìm kiếm địa chỉ tự động qua Mapbox API (Ưu tiên TP.HCM)
    search_text = clean_str
    if "Hồ Chí Minh" not in search_text and "TPHCM" not in search_text and "Việt Nam" not in search_text:
        search_text += ", Hồ Chí Minh, Việt Nam"
        
    mapbox_token = "pk.eyJ1IjoibWFwYm94LWRlbW8iLCJhIjoiY2p4OTBsNGtwMDJhZDN5b2Nmd3V3dnE2OSJ9.R43s2oOvhg0T4a0Mv1K2mQ"
    mapbox_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(search_text)}.json?access_token={mapbox_token}&country=vn&proximity=106.69,10.77&limit=1"
    try:
        res = requests.get(mapbox_url, timeout=4).json()
        if res.get("features"):
            coords = res["features"][0]["center"]  # Mapbox trả về [lon, lat]
            return (round(coords[1], 6), round(coords[0], 6))
    except:
        pass

    return None

# ---------------------------------------------------------
# 2. GIAO DIỆN & CẤU HÌNH ĐẦU VÀO
# ---------------------------------------------------------
st.title("🗺️ Lập Kế Hoạch & Tối Ưu Tuyến Đường Du Lịch")
st.caption("Ứng dụng thuật toán Vét cạn (Brute Force) & Mạng lưới Giao thông Đường bộ OSRM")

st.sidebar.header("📍 Cấu hình Lộ trình")

# 1. Nhập điểm xuất phát
start_input = st.sidebar.text_input(
    "1. Điểm xuất phát (Địa chỉ/Tọa độ/Link Maps):",
    value="10.6865, 106.5942",
    help="Bạn có thể dán tọa độ GPS, gõ địa chỉ hoặc dán đường link Google Maps"
)

# 2. Nhập số lượng điểm đến
num_destinations = st.sidebar.number_input(
    "2. Số lượng điểm muốn đến:",
    min_value=2,
    max_value=8,
    value=3,
    step=1
)

st.sidebar.subheader("3. Nhập danh sách các điểm tham quan:")

default_places = [
    "Dinh Độc Lập, Quận 1",
    "Chợ Bến Thành, Quận 1",
    "Chùa Bát Bửu Phật Đài, Bình Chánh",
    "Bến Nhà Rồng, Quận 4",
    "Khu di tích Lăng Le Bàu Cò, Bình Chánh",
    "Công viên Lê Thị Riêng, Quận 10",
    "Đầm Sen, Quận 11",
    "Bưu điện Trung tâm Sài Gòn"
]

destination_inputs = []
for i in range(num_destinations):
    default_val = default_places[i] if i < len(default_places) else ""
    dest_str = st.sidebar.text_input(f"Địa điểm {i+1}:", value=default_val, key=f"dest_{i}")
    destination_inputs.append(dest_str)

# ---------------------------------------------------------
# 3. TÍNH TOÁN, TỐI ƯU VÀ VẼ BẢN ĐỒ LỘ TRÌNH THỰC TẾ
# ---------------------------------------------------------
if st.sidebar.button("🚀 Bắt đầu tối ưu tuyến đường", type="primary"):
    with st.spinner("Đang truy xuất tọa độ và vẽ tuyến đường giao thông thực tế..."):
        
        # Bước A: Giải mã tọa độ Điểm xuất phát
        start_coords = smart_geocode(start_input)
        if not start_coords:
            st.error("❌ Không thể xác định vị trí Điểm xuất phát. Vui lòng kiểm tra lại!")
            st.stop()
            
        # Bước B: Giải mã tọa độ các điểm đến
        valid_points = [("Điểm xuất phát", start_coords)]
        geocode_table = [{"Mục": "Xuất phát", "Địa chỉ nhập": start_input, "Tọa độ GPS": f"{start_coords[0]}, {start_coords[1]}"}]
        has_error = False

        for i, dest_text in enumerate(destination_inputs):
            if not dest_text.strip():
                st.warning(f"⚠️ Địa điểm {i+1} đang trống!")
                has_error = True
                continue
                
            coords = smart_geocode(dest_text)
            if coords:
                valid_points.append((dest_text.strip(), coords))
                geocode_table.append({"Mục": f"Điểm {i+1}", "Địa chỉ nhập": dest_text, "Tọa độ GPS": f"{coords[0]}, {coords[1]}"})
            else:
                st.error(f"❌ Không tìm thấy tọa độ cho: '{dest_text}'")
                has_error = True

        if has_error or len(valid_points) - 1 < 2:
            st.warning("⚠️ Cần ít nhất 2 địa điểm hợp lệ để tiến hành tối ưu.")
            st.stop()

        # Hiển thị Bảng Tọa độ trích xuất thành công
        st.subheader("📌 Tọa độ GPS thực tế của các địa điểm:")
        st.dataframe(geocode_table, use_container_width=True)

        # Bước C: Lấy Ma trận Khoảng cách Đường bộ (Driving Matrix) từ OSRM
        coords_str = ";".join([f"{lon},{lat}" for name, (lat, lon) in valid_points])
        osrm_table_url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=distance"
        
        try:
            res_table = requests.get(osrm_table_url, timeout=5).json()
            if "distances" in res_table:
                # Chuyển đổi mét -> km
                matrix = [[round(d / 1000.0, 2) for d in row] for row in res_table["distances"]]
                
                # Thuật toán Vét cạn (Brute Force)
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
                
                # Bước D: Hiển thị Kết quả
                st.divider()
                st.success(f"🎉 **Đã hoàn thành tối ưu!** Tổng quãng đường lái xe thực tế: **{round(best_dist, 2)} km**")
                
                # 1. Thứ tự di chuyển
                st.subheader("📋 Thứ tự di chuyển tối ưu đề xuất:")
                ordered_points = [valid_points[idx] for idx in best_path]
                
                gmaps_coords = []
                for step, (name, coords) in enumerate(ordered_points):
                    gmaps_coords.append(f"{coords[0]},{coords[1]}")
                    if step == 0:
                        st.write(f"🚩 **Điểm xuất phát:** {name} *(Tọa độ: {coords[0]}, {coords[1]})*")
                    elif step == len(ordered_points) - 1:
                        st.write(f"🏁 **Trở về:** Điểm xuất phát")
                    else:
                        st.write(f"🔹 **Bước {step}:** {name} *(Tọa độ: {coords[0]}, {coords[1]})*")

                # Link mở Google Maps
                gmaps_url = f"https://www.google.com/maps/dir/{'/'.join(gmaps_coords)}"
                st.markdown(f"[🔗 **Mở Lộ trình này trên Google Maps Navigation**]({gmaps_url})")

                # 2. Lấy hình dạng tuyến đường giao thông (Polylines/Route) và Vẽ Bản đồ Folium
                st.divider()
                st.subheader("🗺️ Bản đồ mô phỏng đường đi ngoài thực tế (Road Network Route)")
                st.caption("Các đường nét đứt màu xanh navy bám sát theo từng con phố, ngã tư thực tế chứ không phải đường thẳng.")

                # Khởi tạo bản đồ Folium đặt góc nhìn tại điểm xuất phát
                m = folium.Map(location=start_coords, zoom_start=12, tiles="OpenStreetMap")
                
                # Đánh dấu các ghim (Markers) trên bản đồ
                for step, (name, coords) in enumerate(ordered_points[:-1]): # Bỏ điểm cuối trùng điểm đầu
                    icon_color = "red" if step == 0 else "blue"
                    popup_text = f"Xuất phát: {name}" if step == 0 else f"Điểm {step}: {name}"
                    folium.Marker(
                        location=coords,
                        popup=popup_text,
                        tooltip=f"{step}. {name}",
                        icon=folium.Icon(color=icon_color, icon="info-sign" if step != 0 else "home")
                    ).add_to(m)

                # Truy vấn OSRM Route Service để vẽ đường cong thực tế giữa các điểm nối tiếp nhau
                route_coords_str = ";".join([f"{lon},{lat}" for name, (lat, lon) in ordered_points])
                osrm_route_url = f"http://router.project-osrm.org/route/v1/driving/{route_coords_str}?overview=full&geometries=geojson"
                
                res_route = requests.get(osrm_route_url, timeout=5).json()
                if "routes" in res_route and len(res_route["routes"]) > 0:
                    geometry = res_route["routes"][0]["geometry"]["coordinates"]
                    # Chuyển [lon, lat] từ GeoJSON thành [lat, lon] cho Folium
                    folium_line = [[lat, lon] for lon, lat in geometry]
                    
                    # Vẽ đường lộ giao thông thực tế lên bản đồ
                    folium.PolyLine(
                        folium_line,
                        color="#1A365D",
                        weight=5,
                        opacity=0.8,
                        dash_array='10',
                        tooltip="Tuyến đường di chuyển thực tế"
                    ).add_to(m)

                # Hiển thị Bản đồ tương tác trên web
                st_folium(m, width=1100, height=500)

        except Exception as e:
            st.error(f"Lỗi khi xử lý dữ liệu bản đồ đường bộ OSRM: {e}")
