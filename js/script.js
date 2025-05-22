document.addEventListener('DOMContentLoaded', function() {
    const itemsContainer = document.getElementById('itemsContainer');
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const itemOverlay = document.getElementById('itemOverlay');
    const closeOverlay = document.getElementById('closeOverlay');
    const rareTypeFilter = document.getElementById('rareTypeFilter');
    const itemTypeFilter = document.getElementById('itemTypeFilter');
    const collectionTypeFilter = document.getElementById('collectionTypeFilter');
    
    let itemsData = [];
    
    // Load item data
    fetch('itemData.json')
        .then(response => response.json())
        .then(data => {
            itemsData = data;
            displayItems(itemsData);
        })
        .catch(error => console.error('Error loading item data:', error));
    
    // Display items in grid
    function displayItems(items) {
        itemsContainer.innerHTML = '';
        
        items.forEach(item => {
            const itemCard = document.createElement('div');
            itemCard.className = 'item-card';
            
            const itemImage = document.createElement('img');
            itemImage.className = 'item-image';
            itemImage.src = `ICONS/${item.itemID}.png`;
            itemImage.alt = item.description;
            itemImage.onerror = function() {
                this.src = 'placeholder.png'; // Fallback if image doesn't exist
            };
            
            const itemInfo = document.createElement('div');
            itemInfo.className = 'item-info';
            itemInfo.textContent = item.description;
            
            itemCard.appendChild(itemImage);
            itemCard.appendChild(itemInfo);
            
            itemCard.addEventListener('click', () => showItemDetails(item));
            
            itemsContainer.appendChild(itemCard);
        });
    }
    
    // Show item details in overlay
    function showItemDetails(item) {
        document.getElementById('overlayTitle').textContent = item.description;
        document.getElementById('overlayDescription').textContent = item.description2;
        document.getElementById('overlayId').textContent = item.itemID;
        document.getElementById('overlayIcon').textContent = item.icon;
        document.getElementById('overlayRare').textContent = item.Rare;
        document.getElementById('overlayUnique').textContent = item.isUnique ? 'Yes' : 'No';
        document.getElementById('overlayItemType').textContent = item.itemType;
        document.getElementById('overlayCollectionType').textContent = item.collectionType;
        
        const overlayImage = document.getElementById('overlayImage');
        overlayImage.src = `ICONS/${item.itemID}.png`;
        overlayImage.alt = item.description;
        overlayImage.onerror = function() {
            this.src = 'placeholder.png';
        };
        
        itemOverlay.style.display = 'flex';
    }
    
    // Close overlay
    closeOverlay.addEventListener('click', () => {
        itemOverlay.style.display = 'none';
    });
    
    // Search functionality
    function performSearch() {
        const searchTerm = searchInput.value.toLowerCase();
        const rareFilter = rareTypeFilter.value;
        const itemTypeFilterValue = itemTypeFilter.value;
        const collectionTypeFilterValue = collectionTypeFilter.value;
        
        const filteredItems = itemsData.filter(item => {
            // Search term matching
            const matchesSearch = 
                item.itemID.toString().includes(searchTerm) ||
                item.description.toLowerCase().includes(searchTerm) ||
                item.icon.toLowerCase().includes(searchTerm);
            
            // Filter matching
            const matchesRare = rareFilter === 'ALL' || item.Rare === rareFilter;
            const matchesItemType = itemTypeFilterValue === 'ALL' || item.itemType === itemTypeFilterValue;
            const matchesCollectionType = collectionTypeFilterValue === 'ALL' || item.collectionType === collectionTypeFilterValue;
            
            return matchesSearch && matchesRare && matchesItemType && matchesCollectionType;
        });
        
        displayItems(filteredItems);
    }
    
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Filter change events
    rareTypeFilter.addEventListener('change', performSearch);
    itemTypeFilter.addEventListener('change', performSearch);
    collectionTypeFilter.addEventListener('change', performSearch);
});
