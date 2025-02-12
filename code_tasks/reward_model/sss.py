from datasets import load_dataset

dataset = load_dataset('/Users/elena/Documents/sibnn/tbank/Reward_Model_Dataset')
print(dataset.features)


Dataset({
    features: ['focal', 'test', 'label', 'text', 'input_ids', 'attention_mask'],
    num_rows: 2613
})
