import streamlit as st
import itertools
import requests

# ---------------------------------------------------------
# 1. KHO DỮ LIỆU ĐỊA ĐIỂM (Bổ sung Tọa độ & Lời giới thiệu ngắn)
# ---------------------------------------------------------
POI_DATA = {
    "Trường THPT (Điểm xuất phát)": {
        "coords": (10.6865, 106.5942),
        "desc": "Điểm tập kết và xuất phát hành trình."
    },
    "Khu di tích Lăng Le - Bàu Cò": {
        "coords": (10.7028, 106.5358),
        "desc": "Di tích lịch sử cấp Quốc gia, nơi ghi dấu chiến công vang dội của quân dân Bình Chánh trong thời kỳ kháng chiến chống Pháp (1948)."
    },
    "Chùa Phật Lớn (Bát Bửu Phật Đài)": {
        "coords": (10.7291, 106.5297),
        "desc": "Nơi thờ tượng Phật Thích Ca cao 7m uy nghiêm, không gian thanh tĩnh thu hút đông đảo du khách hành hương và chiêm bái."
    },
    "Di tích Dân công hỏa tuyến Mậu Thân": {
        "coords": (10.7150, 106.5410),
        "desc": "Nơi tưởng niệm sự hy sinh anh dũng của 32 nữ dân công hỏa tuyến trong cuộc Tổng tiến công và nổi dậy Xuân Mậu Thân 1968."
    },
    "Dinh Độc Lập": {
        "coords": (10.7769, 106.6953),
        "desc": "Di tích quốc gia đặc biệt, biểu tượng lịch sử ghi dấu sự kiện Giải phóng miền Nam, thống nhất đất nước ngày 30/04/1975."
    },
    "Bến Nhà Rồng": {
        "coords": (10.7681, 106.7068),
        "desc": "Bảo tàng Hồ Chí Minh – nơi Bác Hồ ra đi tìm đường cứu nước năm 1911, nằm bên bờ sông Sài Gòn thơ mộng."
    }
}

# ---------------------------------------------------------
# 2. HÀM TỰ ĐỘNG TÍNH KHOẢNG CÁCH QUA API
# ---------------------------------------------------------
def get_distance_matrix(selected_coords):
    n = len(selected_coords)
    coords_str = ";".join([f"{lon},{lat}" for lat, lon in selected_coords])
    url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=distance"
    
    try:
        res = requests.get(url, timeout=5).json()
        distances = res.get("distances", [])
        matrix = [[round(distances[i][j] / 1000.0, 2) for j in range(n)] for i in range(n)]
        return matrix
    except:
        return None

# ---------------------------------------------------------
# 3. GIAO DIỆN WEB STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="Tối ưu tuyến đường du lịch", page_icon="🗺️", layout="wide")

st.title("🗺️ HỆ THỐNG TỐI ƯU HÓA TUYẾN ĐƯỜNG DU LỊCH TRẢI NGHIỆM")
st.caption("Ứng dụng Lý thuyết đồ thị kết hợp API bản đồ giúp xây dựng lộ trình tham quan tối ưu.")

all_places = list(POI_DATA.keys())
start_place = all_places[0]

# Chia màn hình thành 2 cột: Cột trái chọn điểm/kết quả, Cột phải xem giới thiệu địa điểm
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1. Tích chọn điểm tham quan:")
    st.info(f"📍 **Điểm xuất phát:** {start_place}")
    
    selected_places = st.multiselect(
        "Vui lòng chọn các địa điểm bạn muốn ghé thăm:",
        options=all_places[1:],
        default=all_places[1:3]
    )
    
    btn_run = st.button("🚀 TÌM LỘ TRÌNH TỐI ƯU", type="primary", use_container_width=True)

# Hiển thị thông tin giới thiệu ngắn gọn ở cột bên phải
with col_right:
    st.subheader("📖 Thông tin các địa điểm đã chọn:")
    if not selected_places:
        st.write("*Chưa chọn địa điểm nào.*")
    else:
        for place in selected_places:
            with st.expander(f"📍 **{place}**", expanded=True):
                st.write(POI_DATA[place]["desc"])

# Xử lý khi bấm nút tính toán
if btn_run:
    if not selected_places:
        st.warning("Vui lòng chọn ít nhất 1 địa điểm tham quan!")
    else:
        full_list = [start_place] + selected_places
        coords_list = [POI_DATA[place]["coords"] for place in full_list]
        
        with st.spinner("Đang tính toán tuyến đường ngắn nhất..."):
            dist_matrix = get_distance_matrix(coords_list)
            
            if dist_matrix:
                nodes_to_visit = list(range(1, len(full_list)))
                best_dist = float('inf')
                best_route = []
                
                for perm in itertools.permutations(nodes_to_visit):
                    current_route = [0] + list(perm) + [0]
                    current_dist = sum(dist_matrix[current_route[i]][current_route[i+1]] for i in range(len(current_route)-1))
                    
                    if current_dist < best_dist:
                        best_dist = current_dist
                        best_route = current_route
                
                st.divider()
                st.success(f"✅ **ĐÃ TÌM THẤY LỘ TRÌNH TỐI ƯU NHẤT!** (Tổng quãng đường: **{best_dist:.2f} km**)")
                
                # Hiển thị thứ tự đi chi tiết
                st.subheader("🚩 Lộ trình di chuyển đề xuất:")
                route_names = [full_list[i] for i in best_route]
                
                for idx, name in enumerate(route_names):
                    if idx == 0:
                        st.markdown(f"🚩 **Xuất phát:** {name}")
                    elif idx == len(route_names) - 1:
                        st.markdown(f"🏁 **Kết thúc:** Quay về {name}")
                    else:
                        st.markdown(f"➡️ **Chặng {idx}:** {name}")
                        st.caption(f"💡 *Tóm tắt:* {POI_DATA[name]['desc']}")
            else:
                st.error("Không thể kết nối dịch vụ bản đồ. Vui lòng thử lại!")
