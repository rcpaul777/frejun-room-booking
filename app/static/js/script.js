document.addEventListener('DOMContentLoaded', () => {
    const bookingForm = document.getElementById('bookingForm');
    const roomTypeSelect = document.getElementById('roomType');
    const dateInput = document.getElementById('date');
    const startTimeInput = document.getElementById('startTime');
    const endTimeInput = document.getElementById('endTime');
    
    // Set min date to today
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
    
    // Check available rooms when inputs change
    const checkAvailability = async () => {
        if (dateInput.value && startTimeInput.value && endTimeInput.value && roomTypeSelect.value) {
            try {
                const response = await fetch(`/api/v1/rooms/available/?` + new URLSearchParams({
                    slot_date: dateInput.value,
                    slot_start: startTimeInput.value,
                    slot_end: endTimeInput.value,
                    room_type: roomTypeSelect.value
                }));
                
                if (response.ok) {
                    const rooms = await response.json();
                    updateRoomsTable(rooms);
                }
            } catch (error) {
                console.error('Error checking availability:', error);
            }
        }
    };
    
    [roomTypeSelect, dateInput, startTimeInput, endTimeInput].forEach(input => {
        input.addEventListener('change', checkAvailability);
    });
    
    // Handle form submission
    bookingForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const bookingData = {
            room_type: roomTypeSelect.value,
            slot_date: dateInput.value,
            slot_start: startTimeInput.value,
            slot_end: endTimeInput.value,
            user_id: parseInt(document.getElementById('userId').value)
        };
        
        try {
            const response = await fetch('/api/v1/bookings/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(bookingData)
            });
            
            if (response.ok) {
                const result = await response.json();
                alert('Room booked successfully!');
                bookingForm.reset();
                checkAvailability();
            } else {
                const error = await response.json();
                alert('Error booking room: ' + error.detail);
            }
        } catch (error) {
            console.error('Error submitting booking:', error);
            alert('Error submitting booking. Please try again.');
        }
    });
    
    function updateRoomsTable(rooms) {
        const tbody = document.querySelector('#availableRooms tbody');
        tbody.innerHTML = '';
        
        rooms.forEach(room => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${room.id}</td>
                <td>${room.room_type}</td>
                <td>${room.capacity}</td>
                <td>${room.name}</td>
            `;
            tbody.appendChild(row);
        });
        
        if (rooms.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="4" class="text-center">No rooms available</td>';
            tbody.appendChild(row);
        }
    }
});
