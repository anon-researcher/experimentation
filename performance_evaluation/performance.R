library(tidyverse)

data <- read_csv("overall_results.csv")

# View(data)
data$heuristic[data$strategyID >= 0 & data$strategyID <= 4] = 'Subtree'
data$heuristic[data$strategyID >= 5 & data$strategyID <= 7] = 'RTA'
data$heuristic[data$strategyID >= 8 & data$strategyID <= 11] = 'Hybrid'

data$strategyName[data$strategyID == 0] = 'ST'
data$strategyName[data$strategyID == 4] = 'ST Ext.'
data$strategyName[data$strategyID == 5] = 'RTA'
data$strategyName[data$strategyID == 7] = 'RTA Ext.'
data$strategyName[data$strategyID == 9] = 'HYB'
data$strategyName[data$strategyID == 11] = 'HYB Ext.'

data$algorithmDurationSec = round(data$algorithmDuration / 1000, 3)
data$strategyID = as.factor(data$strategyID)
data$deviation = as.factor(data$deviation)

broad = data %>% filter(variation == 'broad', depth <= 10)
deep = data %>% filter(variation == 'deep', depth <= 23)
filtered = data %>% filter((variation == 'broad' & depth <= 10) | (variation == 'deep' & depth <= 23))

View(filtered)

# --------------------------------------------------------------------
# pick the best variant of each heuristic and display
maxDuration = 45

dev = 30
maxNodes = 30000

strategies = c(0,4,5,7,9,11)

preselection <- filtered %>%
   filter(strategyID %in% strategies, deviation == dev, algorithmDurationSec <= maxDuration, nodes <= maxNodes) %>%
   select(strategyID, algorithmDurationSec, variation, nodes, heuristic) %>%
   group_by(strategyID, variation, nodes, heuristic) %>%
   summarise(duration_mean=mean(algorithmDurationSec),
             duration_sd = sd(algorithmDurationSec),
             count = n()) 

selection = preselection %>%
   group_by(variation, nodes, heuristic) %>%
   summarise(run=min(duration_mean),
             count = n())

# method = "gam", formula = y ~ s(x, bs = "cs")

ggplot(data = selection, aes(x = run, y = nodes, color=variation, shape=heuristic)) +
   theme_bw() +
   geom_line(aes(group=nodes), color="black") + 
   geom_point(size=2.5) + 
   geom_smooth(method = "loess", formula=y ~ log(x), aes(group=variation)) +
   # geom_path(aes(x=run, y=nodes)) +
   ylab("Number of Nodes in Difference Graph") +
   xlab("Execution Time of Heuristics [in Seconds]") +
   theme(axis.text = element_text(colour="black", size=10), axis.title=element_text(size=11,face="bold")) +
   theme(legend.position=c(0.87,0.29), 
         legend.text = element_text(size=11),
         legend.background = element_rect(fill="white", size=.3, linetype="solid", colour = "black")) +
   guides(color=guide_legend(title="Graph Structure"),
          shape=guide_legend(title="Heuristic")) +
   ggsave(paste("runtime_broad_deep_dev", dev, "_n", maxNodes,".pdf", sep=""), width = 6.20, height = 4.5, units="in")

# ------------------
# get an individual run:

var = "deep"
freq = "midlow"
dep = 19
# should be 6631 nodes

deviations = c(0,30)
strategies = c(0,4,5,7,9,11)

individual = filtered %>%
   filter(strategyID %in% strategies) %>%
   filter(deviation %in% deviations) %>%
   filter(variation == var, frequency == freq, depth == dep)

ggplot(data = individual, aes(x = strategyName, y = algorithmDurationSec, fill=deviation)) +
   theme_bw() +
   coord_flip() +
   geom_boxplot() + 
   xlab("Heuristic") +
   ylab("Execution Time [in Seconds]") +
   theme(axis.text = element_text(colour="black", size=11), axis.title=element_text(size=12,face="bold")) +
   theme(legend.position="bottom",
         legend.background = element_rect(fill="white", size=.3, linetype="solid"),
         legend.text = element_text(size=12)) +
   guides(fill=guide_legend(title="Percentage of Endpoints causing Performance Deviations:")) + 
   ggsave(paste("boxplot_deep_", freq, "_", dep, ".pdf", sep=""), width = 6.20, height = 4.5, units="in")
