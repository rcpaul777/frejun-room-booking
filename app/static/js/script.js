document.addEventListener('DOMContentLoaded', () => {
    // --- Interactive Office Blueprint Map ---
    async function fetchOfficeBlueprintData() {
        // Fetch all rooms and their bookings for today
        const response = await fetch('/api/v1/rooms/status/');
        if (!response.ok) throw new Error('Failed to fetch room status');
        const rooms = await response.json();
        // For chair-level: fetch bookings for today
        const bookingsResp = await fetch('/api/v1/bookings/?limit=200');
        const bookings = bookingsResp.ok ? await bookingsResp.json() : [];
        return { rooms, bookings };
    }

    function renderOfficeBlueprint({ rooms, bookings }, userId) {
        // SVG layout constants
        const width = 600, height = 400;
        const svgNS = 'http://www.w3.org/2000/svg';
        const map = document.createElementNS(svgNS, 'svg');
        map.setAttribute('width', width);
        map.setAttribute('height', height);
        map.setAttribute('viewBox', `0 0 ${width} ${height}`);
        map.style.maxWidth = '100%';
        map.style.background = '#f8f9fa';

        // Helper: get bookings for a room
        function getRoomBookings(roomId) {
            return bookings.filter(b => b.room_id === roomId && b.is_active);
        }
        // Helper: get user booking for a room
        function getUserBooking(roomId) {
            return bookings.find(b => b.room_id === roomId && b.user_id === userId && b.is_active);
        }

        // Layout: 8 private (left), 4 conference (top right), 3 shared (bottom right)
        // --- Private Rooms ---
        for (let i = 0; i < 8; i++) {
            const room = rooms.find(r => r.room_type === 'private' && r.name.endsWith((i+1).toString()));
            if (!room) continue;
            const x = 30;
            const y = 30 + i * 40;
            const booked = !room.is_available;
            const rect = document.createElementNS(svgNS, 'rect');
            rect.setAttribute('x', x);
            rect.setAttribute('y', y);
            rect.setAttribute('width', 70);
            rect.setAttribute('height', 30);
            rect.setAttribute('rx', 7);
            rect.setAttribute('fill', booked ? '#dc3545' : '#198754');
            rect.setAttribute('stroke', '#333');
            rect.setAttribute('stroke-width', 1);
            rect.style.cursor = booked ? 'not-allowed' : 'pointer';
            rect.addEventListener('click', () => {
                if (!booked) handleBookRoom(room);
            });
            // Tooltip
            rect.addEventListener('mouseenter', () => showTooltip(`${room.name}: ${booked ? 'Booked' : 'Available'}`));
            rect.addEventListener('mouseleave', hideTooltip);
            map.appendChild(rect);
            // Label
            const label = document.createElementNS(svgNS, 'text');
            label.setAttribute('x', x + 35);
            label.setAttribute('y', y + 20);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('font-size', '12');
            label.setAttribute('fill', '#222');
            label.textContent = `P${i+1}`;
            map.appendChild(label);
        }
        // --- Conference Rooms ---
        for (let i = 0; i < 4; i++) {
            const room = rooms.find(r => r.room_type === 'conference' && r.name.endsWith((i+1).toString()));
            if (!room) continue;
            const x = 150 + i * 100;
            const y = 30;
            const booked = !room.is_available;
            // Room rectangle
            const rect = document.createElementNS(svgNS, 'rect');
            rect.setAttribute('x', x);
            rect.setAttribute('y', y);
            rect.setAttribute('width', 80);
            rect.setAttribute('height', 50);
            rect.setAttribute('rx', 10);
            rect.setAttribute('fill', booked ? '#dc3545' : '#198754');
            rect.setAttribute('stroke', '#333');
            rect.setAttribute('stroke-width', 1);
            rect.style.cursor = booked ? 'not-allowed' : 'pointer';
            rect.addEventListener('click', () => {
                if (!booked) handleBookRoom(room);
            });
            rect.addEventListener('mouseenter', () => showTooltip(`${room.name}: ${booked ? 'Booked' : 'Available'}`));
            rect.addEventListener('mouseleave', hideTooltip);
            map.appendChild(rect);
            // Label
            const label = document.createElementNS(svgNS, 'text');
            label.setAttribute('x', x + 40);
            label.setAttribute('y', y + 30);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('font-size', '13');
            label.setAttribute('fill', '#222');
            label.textContent = `C${i+1}`;
            map.appendChild(label);
            // Chairs (15 per room, 3 rows of 5)
            const roomBookings = getRoomBookings(room.id);
            for (let c = 0; c < 15; c++) {
                const cx = x + 15 + (c % 5) * 13;
                const cy = y + 60 + Math.floor(c / 5) * 13;
                const chairBooked = c < roomBookings.length;
                const chair = document.createElementNS(svgNS, 'circle');
                chair.setAttribute('cx', cx);
                chair.setAttribute('cy', cy);
                chair.setAttribute('r', 5);
                chair.setAttribute('fill', chairBooked ? '#dc3545' : '#198754');
                chair.setAttribute('stroke', '#555');
                chair.setAttribute('stroke-width', 0.7);
                map.appendChild(chair);
            }
        }
        // --- Shared Desks ---
        for (let i = 0; i < 3; i++) {
            const room = rooms.find(r => r.room_type === 'shared' && r.name.endsWith((i+1).toString()));
            if (!room) continue;
            const x = 150 + i * 120;
            const y = 300;
            // Desk rectangle
            const rect = document.createElementNS(svgNS, 'rect');
            rect.setAttribute('x', x);
            rect.setAttribute('y', y);
            rect.setAttribute('width', 90);
            rect.setAttribute('height', 30);
            rect.setAttribute('rx', 7);
            rect.setAttribute('fill', '#f0ad4e');
            rect.setAttribute('stroke', '#333');
            rect.setAttribute('stroke-width', 1);
            map.appendChild(rect);
            // Label
            const label = document.createElementNS(svgNS, 'text');
            label.setAttribute('x', x + 45);
            label.setAttribute('y', y + 20);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('font-size', '12');
            label.setAttribute('fill', '#222');
            label.textContent = `SD${i+1}`;
            map.appendChild(label);
            // 4 chairs per desk
            const roomBookings = getRoomBookings(room.id);
            for (let c = 0; c < 4; c++) {
                const cx = x + 20 + c * 15;
                const cy = y + 40;
                const chairBooked = c < roomBookings.length;
                const chair = document.createElementNS(svgNS, 'circle');
                chair.setAttribute('cx', cx);
                chair.setAttribute('cy', cy);
                chair.setAttribute('r', 6);
                chair.setAttribute('fill', chairBooked ? '#dc3545' : '#198754');
                chair.setAttribute('stroke', '#555');
                chair.setAttribute('stroke-width', 0.7);
                map.appendChild(chair);
            }
        }
        // Tooltip
        let tooltip;
        function showTooltip(text) {
            if (!tooltip) {
                tooltip = document.createElement('div');
                tooltip.className = 'office-map-tooltip';
                document.body.appendChild(tooltip);
            }
            tooltip.textContent = text;
            tooltip.style.display = 'block';
        }
        function hideTooltip() {
            if (tooltip) tooltip.style.display = 'none';
        }
        // Place tooltip near mouse
        map.addEventListener('mousemove', e => {
            if (tooltip && tooltip.style.display === 'block') {
                tooltip.style.left = (e.clientX + 10) + 'px';
                tooltip.style.top = (e.clientY - 10) + 'px';
            }
        });
        // Booking handler
        function handleBookRoom(room) {
            if (!confirm(`Book ${room.name}?`)) return;
            // Open booking modal or send booking request (simplified)
            // For demo: book for today, 09:00-10:00
            fetch('/api/v1/bookings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    room_type: room.room_type,
                    slot_date: new Date().toISOString().slice(0,10),
                    slot_start: '09:00',
                    slot_end: '10:00',
                    user_id: userId
                })
            }).then(r => r.json()).then(res => {
                alert('Booking successful!');
                loadOfficeBlueprint(userId);
            }).catch(() => alert('Booking failed.'));
        }
        return map;
    }

    async function loadOfficeBlueprint(userId) {
        const container = document.getElementById('officeMapZoomArea');
        if (!container) return;
        try {
            const data = await fetchOfficeBlueprintData();
            container.innerHTML = '';
            container.appendChild(renderOfficeBlueprint(data, userId));
        } catch (e) {
            container.innerHTML = '<div class="text-danger w-100 text-center" style="font-size:1.1rem;position:absolute;top:50%;left:0;right:0;transform:translateY(-50%);">Failed to load the office map.</div>';
        }
    }

    // On dashboard load, get userId and load map
    window.addEventListener('DOMContentLoaded', () => {
        // userId will be injected by Jinja in dashboard.html
        if (window.officeUserId) {
            loadOfficeBlueprint(window.officeUserId);
        }
    });
});
