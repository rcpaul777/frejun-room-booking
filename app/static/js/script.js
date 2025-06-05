// Simple booking logic, no effects

document.addEventListener('DOMContentLoaded', function() {
    // Set date input to today by default
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        dateInput.value = `${yyyy}-${mm}-${dd}`;
    }

    // Helper: 12-hour slot formatting
    function getSlots() {
        const slots = [];
        for (let h = 9; h < 18; h++) {
            let start = h;
            let end = h + 1;
            let ampmStart = start < 12 ? 'AM' : 'PM';
            let ampmEnd = end < 12 ? 'AM' : 'PM';
            let start12 = start % 12 === 0 ? 12 : start % 12;
            let end12 = end % 12 === 0 ? 12 : end % 12;
            slots.push({
                value: `${String(start).padStart(2, '0')}:00-${String(end).padStart(2, '0')}:00`,
                label: `${start12}:00 ${ampmStart} - ${end12}:00 ${ampmEnd}`
            });
        }
        return slots;
    }

    // Populate time slots
    const slotSelect = document.getElementById('slot');
    if (slotSelect) {
        slotSelect.innerHTML = '';
        getSlots().forEach(slot => {
            const opt = document.createElement('option');
            opt.value = slot.value;
            opt.textContent = slot.label;
            slotSelect.appendChild(opt);
        });
    }

    // Dynamic room/team/seat dropdowns
    const roomType = document.getElementById('roomType');
    const roomDropdownSection = document.getElementById('roomDropdownSection');
    let userTeams = [];
    let availableRooms = [];
    let availableSeats = [];
    let userId = null;
    const bookBtn = document.getElementById('bookBtn');

    // Fetch user info (assume backend injects window.currentUserId)
    if (window.currentUserId) userId = window.currentUserId;

    function checkBookButtonState() {
        // Disable book button if any required field is empty
        const type = roomType.value;
        const date = document.getElementById('date').value;
        const slot = document.getElementById('slot').value;
        let requiredFilled = type && date && slot;
        if (type === 'private' && document.getElementById('roomId')) {
            requiredFilled = requiredFilled && document.getElementById('roomId').value;
        } else if (type === 'conference' && document.getElementById('teamId')) {
            requiredFilled = requiredFilled && document.getElementById('teamId').value;
        } else if (type === 'shared' && document.getElementById('roomId')) {
            requiredFilled = requiredFilled && document.getElementById('roomId').value;
        }
        bookBtn.disabled = !requiredFilled;
    }

    function renderRoomDropdowns() {
        roomDropdownSection.innerHTML = '';
        const type = roomType.value;
        if (!type) {
            checkBookButtonState();
            return; // Don't render if not selected
        }
        if (type === 'private') {
            // Fetch available private rooms for selected date/slot
            const date = document.getElementById('date').value;
            const slot = document.getElementById('slot').value;
            const [slot_start, slot_end] = slot.split('-');
            fetch(`/api/v1/rooms/available/?slot_date=${date}&slot_start=${slot_start}&slot_end=${slot_end}&room_type=private`)
                .then(r => r.json()).then(data => {
                    availableRooms = data;
                    if (!data.length) {
                        alert('No private rooms available for the selected slot.');
                        bookBtn.disabled = true;
                        return;
                    }
                    const label = document.createElement('label');
                    label.className = 'form-label';
                    label.textContent = 'Room Number';
                    const select = document.createElement('select');
                    select.className = 'form-select';
                    select.id = 'roomId';
                    select.name = 'roomId';
                    select.required = true;
                    data.forEach(r => {
                        const opt = document.createElement('option');
                        opt.value = r.id;
                        opt.textContent = r.name;
                        select.appendChild(opt);
                    });
                    select.addEventListener('change', checkBookButtonState);
                    roomDropdownSection.appendChild(label);
                    roomDropdownSection.appendChild(select);
                    checkBookButtonState();
                });
        } else if (type === 'conference') {
            // Fetch user's teams
            fetch('/api/v1/teams/my')
                .then(r => r.json()).then(data => {
                    userTeams = data;
                    if (!data.length) {
                        alert('No teams available for conference room booking.');
                        bookBtn.disabled = true;
                        return;
                    }
                    const label = document.createElement('label');
                    label.className = 'form-label';
                    label.textContent = 'Select Team';
                    const select = document.createElement('select');
                    select.className = 'form-select';
                    select.id = 'teamId';
                    select.name = 'teamId';
                    select.required = true;
                    data.forEach(t => {
                        const opt = document.createElement('option');
                        opt.value = t.id;
                        opt.textContent = t.name;
                        select.appendChild(opt);
                    });
                    select.addEventListener('change', checkBookButtonState);
                    roomDropdownSection.appendChild(label);
                    roomDropdownSection.appendChild(select);
                    checkBookButtonState();
                });
        } else if (type === 'shared') {
            // Fetch available shared desks and seats
            const date = document.getElementById('date').value;
            const slot = document.getElementById('slot').value;
            const [slot_start, slot_end] = slot.split('-');
            fetch(`/api/v1/rooms/available/?slot_date=${date}&slot_start=${slot_start}&slot_end=${slot_end}&room_type=shared`)
                .then(r => r.json()).then(data => {
                    availableRooms = data;
                    if (!data.length) {
                        alert('No shared desks available for the selected slot.');
                        bookBtn.disabled = true;
                        return;
                    }
                    const labelRoom = document.createElement('label');
                    labelRoom.className = 'form-label';
                    labelRoom.textContent = 'Shared Desk';
                    const selectRoom = document.createElement('select');
                    selectRoom.className = 'form-select';
                    selectRoom.id = 'roomId';
                    selectRoom.name = 'roomId';
                    selectRoom.required = true;
                    data.forEach(r => {
                        const opt = document.createElement('option');
                        opt.value = r.id;
                        opt.textContent = r.name;
                        selectRoom.appendChild(opt);
                    });
                    selectRoom.addEventListener('change', checkBookButtonState);
                    roomDropdownSection.appendChild(labelRoom);
                    roomDropdownSection.appendChild(selectRoom);
                    checkBookButtonState();
                });
        }
    }

    // Update dropdowns on change
    if (roomType) roomType.addEventListener('change', renderRoomDropdowns);
    if (slotSelect) slotSelect.addEventListener('change', renderRoomDropdowns);
    if (dateInput) dateInput.addEventListener('change', renderRoomDropdowns);

    // Also check book button state on input changes
    if (roomType) roomType.addEventListener('change', checkBookButtonState);
    if (slotSelect) slotSelect.addEventListener('change', checkBookButtonState);
    if (dateInput) dateInput.addEventListener('change', checkBookButtonState);

    // Initial render
    renderRoomDropdowns();
    checkBookButtonState();

    // Booking form submit
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const type = roomType.value;
            const date = document.getElementById('date').value;
            let slot = document.getElementById('slot').value;
            const [slot_start, slot_end] = slot.split('-');
            let payload = {
                room_type: type,
                slot_date: date,
                slot_start: slot_start,
                slot_end: slot_end
            };
            if (type === 'private') {
                payload.room_id = document.getElementById('roomId').value;
            } else if (type === 'conference') {
                payload.team_id = document.getElementById('teamId').value;
            } else if (type === 'shared') {
                payload.room_id = document.getElementById('roomId').value;
                payload.seat_number = document.getElementById('seatNumber').value;
            }
            const res = await fetch('/api/v1/bookings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const msgDiv = document.getElementById('bookingMsg');
            if (res.ok) {
                const data = await res.json();
                msgDiv.textContent = 'Booking successful! Booking ID: ' + data.id;
                msgDiv.className = 'alert alert-success';
                updateMyBookings();
            } else {
                const err = await res.json();
                msgDiv.textContent = err.detail || 'Booking failed.';
                msgDiv.className = 'alert alert-danger';
            }
        });
    }

    // My Bookings dropdown
    const myBookingsDropdown = document.getElementById('myBookingsDropdown');
    const myBookingsList = document.getElementById('myBookingsList');
    if (myBookingsDropdown) {
        myBookingsDropdown.addEventListener('click', function() {
            myBookingsList.classList.toggle('show');
            if (myBookingsList.classList.contains('show')) updateMyBookings();
        });
    }
    async function updateMyBookings() {
        myBookingsList.innerHTML = 'Loading...';
        const res = await fetch('/api/v1/bookings/');
        if (res.ok) {
            const data = await res.json();
            if (data.length === 0) {
                myBookingsList.textContent = 'No bookings.';
            } else {
                myBookingsList.innerHTML = '';
                data.forEach(b => {
                    const div = document.createElement('div');
                    let info = `Room: ${b.room_id}`;
                    if (b.room_type === 'shared') {
                        info += ` | Seat: ${b.seat_number}`;
                    }
                    info += ` | Date: ${b.slot_date} | ${b.slot_start}-${b.slot_end} | Booking ID: ${b.id}`;
                    div.textContent = info;
                    const cancelBtn = document.createElement('button');
                    cancelBtn.textContent = 'Cancel';
                    cancelBtn.className = 'btn btn-sm btn-danger ms-2';
                    cancelBtn.onclick = async function() {
                        await fetch(`/api/v1/bookings/${b.id}`, { method: 'DELETE' });
                        updateMyBookings();
                        renderRoomDropdowns();
                    };
                    div.appendChild(cancelBtn);
                    myBookingsList.appendChild(div);
                });
            }
        } else {
            myBookingsList.textContent = 'Failed to fetch bookings.';
        }
    }

    // My Teams dropdown
    const myTeamsDropdown = document.getElementById('myTeamsDropdown');
    const myTeamsList = document.getElementById('myTeamsList');
    if (myTeamsDropdown) {
        myTeamsDropdown.addEventListener('click', function() {
            myTeamsList.classList.toggle('show');
            if (myTeamsList.classList.contains('show')) updateMyTeams();
        });
    }
    async function updateMyTeams() {
        myTeamsList.innerHTML = 'Loading...';
        const res = await fetch('/api/v1/teams/my');
        if (res.ok) {
            const data = await res.json();
            if (data.length === 0) {
                myTeamsList.textContent = 'No teams.';
            } else {
                myTeamsList.innerHTML = '';
                data.forEach(t => {
                    const div = document.createElement('div');
                    div.textContent = t.name + ' (ID: ' + t.id + ')';
                    myTeamsList.appendChild(div);
                });
            }
        } else {
            myTeamsList.textContent = 'Failed to fetch teams.';
        }
    }

    // Create Team dropdown
    const createTeamDropdown = document.getElementById('createTeamDropdown');
    const createTeamList = document.getElementById('createTeamList');
    if (createTeamDropdown) {
        createTeamDropdown.addEventListener('click', function() {
            createTeamList.classList.toggle('show');
        });
    }
    const teamSearchInput = document.getElementById('teamSearchInput');
    const teamSearchResults = document.getElementById('teamSearchResults');
    if (teamSearchInput) {
        teamSearchInput.addEventListener('input', async function() {
            const q = teamSearchInput.value;
            if (!q) { teamSearchResults.innerHTML = ''; return; }
            const res = await fetch('/api/v1/users/search?q=' + encodeURIComponent(q));
            if (res.ok) {
                const data = await res.json();
                teamSearchResults.innerHTML = '';
                data.forEach(u => {
                    const div = document.createElement('div');
                    div.textContent = u.name + ' (' + u.email + ')';
                    div.onclick = function() {
                        div.classList.toggle('selected');
                    };
                    teamSearchResults.appendChild(div);
                });
            }
        });
    }
    const createTeamBtn = document.getElementById('createTeamBtn');
    if (createTeamBtn) {
        createTeamBtn.addEventListener('click', async function() {
            const selected = Array.from(teamSearchResults.querySelectorAll('.selected'));
            if (selected.length === 0) return alert('Select at least one user.');
            const memberIds = selected.map(div => div.dataset.userId);
            const name = prompt('Enter team name:');
            if (!name) return;
            const res = await fetch('/api/v1/teams/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, member_ids: memberIds })
            });
            if (res.ok) {
                alert('Team created!');
                updateMyTeams();
            } else {
                alert('Failed to create team.');
            }
        });
    }

    // Available Rooms dropdown
    const availableRoomsDropdown = document.getElementById('availableRoomsDropdown');
    const availableRoomsList = document.getElementById('availableRoomsList');
    if (availableRoomsDropdown) {
        availableRoomsDropdown.addEventListener('click', function() {
            availableRoomsList.classList.toggle('show');
            if (availableRoomsList.classList.contains('show')) updateAvailableRooms();
        });
    }
    async function updateAvailableRooms() {
        const date = document.getElementById('date').value;
        const slot = document.getElementById('slot').value;
        const [slot_start, slot_end] = slot.split('-');
        const type = roomType.value;
        const res = await fetch(`/api/v1/rooms/available/?slot_date=${date}&slot_start=${slot_start}&slot_end=${slot_end}&room_type=${type}`);
        availableRoomsList.innerHTML = '';
        if (res.ok) {
            const data = await res.json();
            if (data.length === 0) {
                availableRoomsList.textContent = 'No available rooms.';
            } else {
                data.forEach(r => {
                    const div = document.createElement('div');
                    div.textContent = `Room: ${r.name} (${r.room_type})`;
                    div.style.display = 'flex';
                    div.style.justifyContent = 'space-between';
                    div.style.alignItems = 'center';
                    const bookBtn = document.createElement('button');
                    bookBtn.textContent = 'Book';
                    bookBtn.className = 'btn btn-sm btn-success ms-2';
                    bookBtn.onclick = async function() {
                        // Prepare booking payload
                        let payload = {
                            room_type: type,
                            slot_date: date,
                            slot_start: slot_start,
                            slot_end: slot_end
                        };
                        if (type === 'private' || type === 'shared') {
                            payload.room_id = r.id;
                        }
                        // For conference, require team selection
                        if (type === 'conference') {
                            // Try to get selected team from booking form
                            const teamSelect = document.getElementById('teamId');
                            if (!teamSelect || !teamSelect.value) {
                                alert('Please select a team in the booking form first.');
                                return;
                            }
                            payload.team_id = teamSelect.value;
                        }
                        // For shared, seat selection is not handled here (auto-assign)
                        const bookingRes = await fetch('/api/v1/bookings/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (bookingRes.ok) {
                            const data = await bookingRes.json();
                            alert('Booking successful! Booking ID: ' + data.id);
                            updateMyBookings();
                            updateAvailableRooms();
                        } else {
                            const err = await bookingRes.json();
                            alert(err.detail || 'Booking failed.');
                        }
                    };
                    div.appendChild(bookBtn);
                    availableRoomsList.appendChild(div);
                });
            }
        } else {
            availableRoomsList.textContent = 'Failed to fetch available rooms.';
        }
    }
});