from ReputationAgent import ReputationAgent
import datetime as dt
import time
import json
import numpy as np
import scipy.stats as stats
import copy


class Adapters():
    def __init__(self, config):

        self.name = config['parameters']['macro_view']
        self.original_config = config
        self.config = config


    def translate(self):
        if self.name == "antons_view":
            return self.antons_view()

    def antons_view(self):

        na= self.config['macro_views']['antons_view']['parameters']['NA']
        #grs= self.config['macro_views']['antons_view']['parameters']['GRs']
        crg= self.config['macro_views']['antons_view']['parameters']['CRg']
        crb= self.config['macro_views']['antons_view']['parameters']['CRb']
        ntg= self.config['macro_views']['antons_view']['parameters']['NTg']
        ntb= self.config['macro_views']['antons_view']['parameters']['NTb']
        nig= self.config['macro_views']['antons_view']['parameters']['NIg']
        nib= self.config['macro_views']['antons_view']['parameters']['NIb']
        na= self.config['macro_views']['antons_view']['parameters']['NA']
        d= self.config['macro_views']['antons_view']['parameters']['D']
        sp= self.config['macro_views']['antons_view']['parameters']['SP']
        sip= self.config['macro_views']['antons_view']['parameters']['SIP']
        plrg= self.config['macro_views']['antons_view']['parameters']['PLRg']
        plrb= self.config['macro_views']['antons_view']['parameters']['PLRb']
        pr= self.config['macro_views']['antons_view']['parameters']['PR']
        npr= self.config['macro_views']['antons_view']['parameters']['NP']
        pmin= self.config['macro_views']['antons_view']['parameters']['Pmin']
        pmax= self.config['macro_views']['antons_view']['parameters']['Pmax']
        gf = self.config['macro_views']['antons_view']['parameters']['GF']

        self.config ['parameters']['num_users'] = na
        # num_bad_agents = na //(gr+1)
        # num_good_agents = gr*num_bad_agents
        #
        #
        # num_good_consumers = (num_good_agents*crg) // (crg + 1)
        # num_good_suppliers = num_good_consumers // crg
        # num_bad_consumers = (num_bad_agents*crb) // (crb + 1)
        # num_bad_suppliers = num_bad_consumers // crb
        #
        # num_consumers = num_good_consumers + num_bad_consumers
        # num_bad_consumers = gf * num_consumers
        # num_good_consumers = num_consumers - num_bad_consumers
        # num_bad_agents = num_bad_consumers + num_bad_suppliers

        # all the above doesnt really work.  GR is no longer needed, now that we have GF.

        num_bad_consumers = int(round((gf*na*crg)/(1.0+crg-gf+((gf*crg)/crb))))
        num_bad_suppliers = int(round(num_bad_consumers/crb))
        num_bad_agents = num_bad_consumers + num_bad_suppliers
        num_good_agents = int(round(na - num_bad_agents))
        num_consumers = int(round(num_bad_consumers/gf))
        num_good_consumers = num_consumers -num_bad_consumers
        num_good_suppliers = num_good_agents - num_good_consumers
        num_suppliers = num_bad_suppliers + num_good_suppliers



        self.config['parameters']['chance_of_criminal']=num_bad_agents /na
        date_time = self.config['parameters']['initial_date']
        pattern = '%d.%m.%Y %H:%M:%S'
        date_tuple = time.strptime(date_time, pattern)
        date = dt.date(date_tuple[0], date_tuple[1], date_tuple[2])
        datestr = date + dt.timedelta(days=d)
        datestr = datestr.strftime(pattern)
        self.config['parameters']['final_date'] = datestr

        self.config['parameters']['chance_of_rating_good2good']=plrg * 0.01
        self.config['parameters']['chance_of_rating_good2bad']=plrb * 0.01

        self.config['parameters']["scam_parameters"]["scam_period"][0] = sp
        self.config['parameters']["scam_parameters"]["scam_inactive_period"][0] = sip


        product_list = ["{0}".format(i) for i in range(npr)]

        x = np.arange(1, npr + 1)

        z = self.config['macro_views']['antons_view']['supplement']['zipf_parameter']
        weights = x ** (-z)
        weights /= weights.sum()
        sample = weights
        #bounded_zipf = stats.rv_discrete(name='bounded_zipf', values=(x, weights))
        #sample = bounded_zipf.rvs(size=npr)

        stdev = self.config['macro_views']['antons_view']['supplement']['amounts_stdev']
        min= self.config['macro_views']['antons_view']['supplement']['amounts_min']
        max=self.config['macro_views']['antons_view']['supplement']['amounts_max']

        new_amounts_good = {p:[sample[i]*nig*npr,stdev, min, max] for i,p in enumerate(product_list)}
        self.config['parameters']['amounts'] = new_amounts_good

        new_amounts_bad = {p:[sample[i]*nib*npr,stdev, min, max] for i,p in enumerate(product_list)}
        self.config['parameters']['criminal_amounts'] = new_amounts_bad

        self.config['parameters']['transactions_per_day'][0]= ntg
        self.config['parameters']['criminal_transactions_per_day'][0]= ntb

        stdev = self.config['macro_views']['antons_view']['supplement']['cobb_douglas_stdev']
        cobb_douglas = {p:[sample[i],stdev] for i,p in enumerate(product_list)}
        self.config['parameters']['cobb_douglas_utilities'] = cobb_douglas

        criminal_cobb_douglas = {p:(sample[i] if p in self.config['parameters']['criminal_category_list'] else 0
                                    ) for i,p in enumerate(product_list)}
        criminal_cobb_douglas = self.normalize_utilities(criminal_cobb_douglas)

        stdev = self.config['macro_views']['antons_view']['supplement']['need_cycle_stdev']
        min= self.config['macro_views']['antons_view']['supplement']['need_cycle_min']
        max=self.config['macro_views']['antons_view']['supplement']['need_cycle_max']

        new_need_cycle = {p:[1/(sample[i]*ntg),stdev, min, max] for i,p in enumerate(product_list)}
        self.config['parameters']['need_cycle'] = new_need_cycle

        sub_product_list = [p for p in product_list if (
                p in self.config['parameters']['criminal_category_list'] )]
        sub_sample = [ sample[int(p)] for p in sub_product_list]
        sub_sample_sum = sum(sub_sample)
        normalized_sample = [s/sub_sample_sum for s in sub_sample]
        norm_tuples = zip(sub_product_list,normalized_sample )

        new_criminal_need_cycle = {p:[1/(s*ntb),stdev, min, max] for p,s in norm_tuples}
        self.config['parameters']['criminal_need_cycle'] = new_criminal_need_cycle

        stdev = self.config['macro_views']['antons_view']['supplement']['price_stdev']

        cycle_min = 1/(sample.max()*ntg)
        cycle_max = 1/(sample.min()*ntg)
        price_factor = 1 if cycle_min == cycle_max else (pmax-pmin)/(cycle_max-cycle_min)
        new_prices = {p:[pmin + ((1/(sample[i]*ntg) )- cycle_min)*price_factor,stdev, pmin, pmax] for i,p in enumerate(product_list)}
        self.config['parameters']['prices'] = new_prices
        new_prices_bad = copy.deepcopy(new_prices)
        self.config['parameters']['criminal_prices'] = new_prices_bad

        transaction_rates = [a[0] for p,a in cobb_douglas.items()]
        amounts = [a[0] for p,a in new_amounts_good.items()]
        prices = [a[0] for p,a in new_prices.items()]

        market_volume = [p*a*t for p, a , t in zip(prices,amounts,transaction_rates) ]
        sum_market_volume = sum(market_volume)
        chance_of_supplying = {p:0  for i,p in enumerate(product_list)} if sum_market_volume== 0 or num_good_agents==0 else {p:(market_volume[i]/sum_market_volume) * (num_good_suppliers/num_good_agents) for i,p in enumerate(product_list)}
        self.config['parameters']['chance_of_supplying']= chance_of_supplying

        transaction_rates = [a for p,a in criminal_cobb_douglas.items()]
        amounts = [a[0] for p,a in new_amounts_bad.items()]
        prices = [a[0] for p,a in new_prices_bad.items()]
        market_volume = [p*a*t for p, a , t in zip(prices,amounts,transaction_rates) ]
        sum_market_volume = sum(market_volume)

        criminal_chance_of_supplying ={p:0  for i,p in enumerate(self.config['parameters']['criminal_category_list'])
            } if sum_market_volume== 0 or num_bad_agents==0 else {p:(
            market_volume[i]/sum_market_volume)* (num_bad_suppliers/num_bad_agents)  for i,p in enumerate(product_list)}
        self.config['parameters']['criminal_chance_of_supplying']= criminal_chance_of_supplying

        mean =  self.config['parameters']['goodness'][0]
        stdev = self.config['parameters']['goodness'][1]
        pneg = 1 / (1 + pr)
        threshold = stats.norm(mean, stdev).ppf(pneg)
        self.config['parameters']['ratings_goodness_thresholds']["0.0"]=threshold

        if self.config['macro_views']['antons_view']['supplement'] ["overwrite_criminal_agent_ring_size"] == "divide_equally":
            self.config['parameters']['criminal_agent_ring_size'][0] = 0 if num_bad_suppliers == 0 else int(round(num_bad_consumers/num_bad_suppliers))

        return self.config



    def normalize_utilities(self,utilities):
        #make all the utilities add to one

        sum_utilities = sum(utilities.values())
        utilities = {k:(v/sum_utilities) for k,v in utilities.items()}
        return utilities